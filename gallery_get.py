# GALLERY_GET is a tool for downloading images from a gallery page.
#
# ABOUT THIS TOOL
# Many sites link each thumbnail to another page for displaying the image,
# which makes batch-downloading impossible (even with browser plugins).
# This tool will crawl the linked pages for the actual image and download them for you.
# Also, this tool can request multiple images at one time
#
# ABOUT THE PLUGINS FOLDER
# the gallery_plugins folder contains settings for different gallery pages
# feel free to add your own plugins for sites not already supported!
#
# Rego Sen
# Aug 22, 2013
#

import os,time,sys,traceback
import re

# Python 3 imports that throw in Python 2
try:
    import queue
    import html.parser as HTMLParser
    from urllib.parse import urlparse
except ImportError:
    # This is Python 2
    import Queue as queue
    import HTMLParser
    from urlparse import urlparse

import threading
from gallery_utils import *
from gallery_plugins import *
import multiprocessing
import calendar

html_parser = HTMLParser.HTMLParser()

QUEUE = queue.Queue()
STANDBY = False
THREADS = []
MAX_ATTEMPTS = 10

TEXTCHARS = ''.join(map(chr, [7,8,9,10,12,13,27] + list(range(0x20, 0x100))))
DESTPATH_FILE = os.path.join(os.path.dirname(str(__file__)), "last_gallery_dest.txt")
DEST_ROOT = unicode_safe(os.getcwd())

EXCEPTION_NOTICE = """An exception occurred!  We can help if you follow these steps:\n
1. Visit https://github.com/regosen/gallery_get/issues
2. Click the "New Issue" button
3. Copy the text between the lines and paste it into the issue.
(If you don't want to share the last line, the rest can still help.)"""
PARAMS = []

def is_binary(urlresponse):
    try:
        return not 'text/html' in urlresponse.headers['Content-Type']
    except:
        return True

def safestr(name):
    name = name.replace(":",";") # to preserve emoticons
    name = "".join(i for i in name if ord(i)<128)
    name = html_parser.unescape(name)
    return re.sub(r"[\/\\\*\?\"\<\>\|]", "", name).strip().rstrip(".")

def is_str(obj):
    return isinstance(obj, str_type)

def safe_makedirs(folder):
    if not os.path.exists(folder):
        os.makedirs(folder)

def safe_unpack(obj, default):
    if is_str(obj):
        return (obj,safestr(default))
    elif obj:
        return (obj[0],safestr(obj[1]))
    else:
        return ("","")

def run_match(match, source, singleItem=False):
    result = []
    if match:
        if is_str(match):
            rematch = re.compile(match, re.I)
            # support for grouped matches
            for curmatch in rematch.finditer(source):
                group = curmatch.groupdict()
                if group:
                    result.append((group['link'],group['basename']))
                else:
                    group = curmatch.groups()
                    if group:
                        result.append(group if len(group) > 1 else group[0])
                    else:
                        result.append(match)
        else:
            result = match(source)
    if singleItem:
        result = result if is_str(result) else result[0] if result else ""
    elif is_str(result):
        result = [result]
    elif hasattr(result, '__iter__'):
        # remove duplicates without affecting order (like set does)
        visited = set()
        visited_add = visited.add
        result = [x for x in result if not (x in visited or visited_add(x))]
    return result if result else []

def safeurl(parent, link):
    if not link.lower().startswith("http"):
        uri=urlparse(parent)
        root = '{uri.scheme}://{uri.netloc}/'.format(uri=uri)
        if link.startswith("//"):
            link = "%s:%s" % (uri.scheme, link)
        elif link.startswith("/") or root.strip('/').lower() == parent.strip('/').lower():
            link = root + link
        else:
            link = os.path.dirname(parent) + "/" + link
    return link.replace("&amp;","&")

def match_plugin(page):
    plugin = PLUGINS["plugin_generic"]
    for modname in PLUGINS.keys():
        if modname == "plugin_generic":
            continue
        cur_plugin = PLUGINS[modname]
        if run_match(cur_plugin.identifier, page):
            plugin = cur_plugin
            break
    if plugin.identifier == "generic":
        if "access denied" in page.lower():
            plugin = None 
    return plugin

class JobInfo(object):
    def __init__(self, plugin=None, subtitle="", path="", redirect="", dest="", index=0):
        self.plugin = plugin
        self.index = index
        self.redirect = redirect
        self.path = path
        self.subtitle = subtitle
        self.attempts = 0
        self.dest = dest
        self.data = None

def start_jobs():
    global STANDBY, THREADS
    if not THREADS:
        STANDBY = True
        for i in range(multiprocessing.cpu_count()):
            t = ImgThread()
            t.start()
            THREADS.append(t)

def flush_jobs():
    global STANDBY, THREADS
    STANDBY = False
    for t in THREADS:
        t.join()
    THREADS = []

def add_job(plugin=None, subtitle="", path="", redirect="", dest="", index=0):
    global QUEUE
    start_jobs()
    QUEUE.put(JobInfo(plugin=plugin, subtitle=subtitle, path=path, redirect=redirect, dest=dest, index=index))



class ImgThread(threading.Thread):
    """Threaded Url Grab"""

    def copyImage(self, info):
        info.attempts += 1
        indexstr = "%03d" % info.index # 001, 002, etc.

        basename = info.subtitle
        if info.plugin and info.plugin.useFilename:
            basename = os.path.basename(info.path).split("?")[0]
        elif not basename or basename == FALLBACK_TITLE:
            basename = indexstr
        elif info.index > 0:
            (basename,ext) = os.path.splitext(basename)
            basename = "%s_%s%s" % (basename, indexstr, ext)

        # copy extension (falling back on jpg)
        if not re.match(r".+\.[a-zA-Z0-9]+\Z", basename):
            ext = ".jpg"
            tokens = info.path.split("?")[0].split("/")[-1].split(".")
            if len(tokens) > 1:
                ext = "." + tokens[-1]
            basename += ext

        try:
            fileInfo = urlopen_safe(info.path)
            modtimestr = fileInfo.headers['last-modified']
            modtime = time.strptime(modtimestr, '%a, %d %b %Y %H:%M:%S %Z')
        except:
            modtime = None

        fileName = os.path.join(info.dest, basename)
        if os.path.exists(fileName):
            # file already exists.  Skip if same size
            srcsize = 0
            try:
                srcsize = int(fileInfo.headers.get("content-length"))
            except:
                print("Skipping " + fileName + " (couldn't compare file size)")
                return True

            destsize = os.stat(fileName).st_size
            if srcsize == destsize:
                print("Skipping " + fileName)
                return True

        if info.attempts == 1:
            print("%s -> %s" % (info.path, fileName))
        else:
            print("%s -> %s (Attempt %d)" % (info.path, fileName, info.attempts))
        if not info.data:
            try:
                info.data = fileInfo.read()
            except:
                # don't bother printing anything, will display next attempt
                return False

        fileInfo.close()
        output = open(fileName,'wb')
        output.write(info.data)
        output.close()
        if modtime is not None:
            lastmod = calendar.timegm(modtime)
            os.utime(fileName, (lastmod, lastmod))
        return os.path.getsize(fileName) > 4096

    def run_internal(self):
        global QUEUE, STANDBY, MAX_ATTEMPTS
        while STANDBY or not QUEUE.empty():
            try:
                info = QUEUE.get(False)
            except:
                time.sleep(0.5)
                continue

            if info.redirect:
                try:
                    response = urlopen_safe(info.redirect)
                except:
                    print("WARNING: Failed to open redirect " + info.redirect)
                    continue
                if is_binary(response):
                    # looks like the redirect page is an actual image
                    info.path = info.redirect
                    info.data = response.read()
                elif info.plugin:
                    jpegs = run_match(info.plugin.direct,response.read().decode('utf-8'))
                    if not jpegs:
                        print("No links found at redirect page!  Check regex.  Redirect URL:")
                        print(info.redirect)
                    elif len(jpegs) == 1 and not info.path:
                        (info.path,info.subtitle) = safe_unpack(jpegs[0],info.subtitle)
                    else:
                        # redirect has multiple links, put them in their own subfolders
                        for idx, path in enumerate(jpegs):
                            (path,subtitle) = safe_unpack(path,info.subtitle)
                            path = safeurl(info.redirect, path)
                            add_job(plugin=info.plugin, path=path, dest=os.path.join(info.dest,subtitle), index=idx+1)
            if info.path:
                info.path = safeurl(info.redirect, info.path)
                while not self.copyImage(info):
                    if info.attempts >= MAX_ATTEMPTS:
                        print("ERROR: Failed to copy " + info.path)
                        break
            QUEUE.task_done()

    def run(self):
        try:
            self.run_internal()
        except:
            print('\n' + '-'*60)
            traceback.print_exc(file=sys.stdout)
            print("Using params: %s" % sys.argv)
            print('-'*60 + '\n')
            print(EXCEPTION_NOTICE)
            os._exit(1)

def download_image(url, fileNameFull):
    try:
        urlBase, fileExtension = os.path.splitext(url)
        fileName = os.path.abspath(fileNameFull)[:255] + fileExtension #full path must be 260 characters or lower
        folder = os.path.dirname(fileName)
        if not os.path.exists(folder):
            os.makedirs(folder)
        elif os.path.exists(fileName):
            print("Skipping " + fileName)
            return folder
        add_job(path=url, dest=folder, subtitle=fileName)
        return folder
    except:
        print("ERROR: Couldn't open URL: " + myurl)
        return False

def run_internal(myurl, folder=DEST_ROOT, useTitleAsFolder=True, allowGenericPlugin=True):
    global QUEUE
    if not myurl:
        print("Nothing to do!")
        return

    try:
        page = urlopen_safe(myurl).read().decode('utf-8')
    except:
        # this could be a direct image
        return download_image(myurl,folder)

    folder = folder.strip()

    ### FIND MATCHING PLUGIN
    plugin = match_plugin(page)
    if plugin == None:
        print("Couldn't access gallery page! Try saving page(s) locally and use local path instead.")
        sys.exit(0)
    elif (not allowGenericPlugin) and (plugin.identifier == "generic"):
        # DON'T USE GENERIC PLUGIN FROM REDDIT_GET
        return False
    else:
        print("Using %s plugin..." % plugin.debugname)

    ### CREATE FOLDER FROM PAGE TITLE
    title = run_match(plugin.title, page, True)
    (title, subtitle) = safe_unpack(title, "")
    title = safestr(title)
    if not title:
        title = FALLBACK_TITLE
    root = ""
    if folder:
        if useTitleAsFolder:
            root = folder
            subtitle = title
        else:
            root = os.path.join(folder, title)
    else:
        root = title


    ### QUEUE JOBS FOR OPENING LINKS
    links = []
    using_redirect = False

    if plugin.redirect:
        links = run_match(plugin.redirect, page)
        if links:
            using_redirect = True
            for idx, link in enumerate(links):
                (link,subtitle) = safe_unpack(link, subtitle)
                link = safeurl(myurl, link)
                safe_makedirs(root)
                add_job(plugin=plugin, redirect=link, dest=root, subtitle=subtitle, index=idx+1)

    if not using_redirect:
        links = run_match(plugin.direct, page)
        if len(links) == 1:
            # don't create folder for only one file
            (root, filename) = os.path.split(root)
            safe_makedirs(root)
            add_job(plugin=plugin, path=links[0], dest=root, subtitle=filename)
        else:
            safe_makedirs(root)
            for idx, link in enumerate(links):
                (link,subtitle) = safe_unpack(link, subtitle)
                link = safeurl(myurl, link)
                add_job(plugin=plugin, path=link, dest=root, subtitle=subtitle, index=idx+1)
    if not links:
        if folder:
            print("No links found at %s, plugin may need updating." % myurl)
        else:
            print("No links found!  Plugin may need updating.")
        print("Sites occasionally change their markup.  Check if this tool has an update.")
        print(" - https://github.com/regosen/gallery_get")
        print(" - pip install gallery_get --update")
    return root


def run_wrapped(myurl, dest, titleAsFolder=False, cacheDest=True, flushJobs=True, allowGenericPlugin=True):
    global DEST_ROOT, PARAMS_DEBUG
    PARAMS_DEBUG = [myurl, dest, titleAsFolder]
    try:
        if cacheDest:
            if dest:
                safeCacheDestination(dest)
            elif os.path.exists(DESTPATH_FILE):
                dest = open(DESTPATH_FILE,"r").read().strip()
            DEST_ROOT = unicode_safe(dest)
        root = run_internal(myurl, dest, titleAsFolder, allowGenericPlugin)
        if flushJobs:
            flush_jobs()
        return root
    except:
        print('\n' + '-'*60)
        traceback.print_exc(file=sys.stdout)
        print("Using params: %s" % PARAMS_DEBUG)
        print('-'*60 + '\n')
        print(EXCEPTION_NOTICE)
        return False

def run_prompted():
    global DEST_ROOT
    myurl = str_input("Input URL: ").strip()
    new_dest = str_input("Destination (%s): " % encode_safe(DEST_ROOT)).strip()
    return run_wrapped(myurl, new_dest if new_dest else DEST_ROOT)

def run(myurl="", dest=""):
    if not myurl:
        return run_prompted()
    else:
        return run_wrapped(myurl, dest)

def safeCacheDestination(dest):
    try:
        open(DESTPATH_FILE,"w").write(dest)
    except:
        open(DESTPATH_FILE,"w").write(dest.encode("utf8"))
cur_file = os.path.basename(str(__file__))
arg_file = sys.argv[0]
if os.path.exists(DESTPATH_FILE):
    DEST_ROOT = unicode_safe(open(DESTPATH_FILE,"r").read().strip())

if arg_file and os.path.basename(arg_file) == cur_file:
    ### DIRECT LAUNCH (not import)
    if len(sys.argv) > 1:
        # use first parameter as url, second (if exists) as dest
        if len(sys.argv) > 2:
            DEST_ROOT = unicode_safe(sys.argv[2])
            safeCacheDestination(DEST_ROOT)
        run_wrapped(sys.argv[1], DEST_ROOT)
    else:
        run_prompted()
