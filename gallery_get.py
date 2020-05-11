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
except ImportError:
    # This is Python 2
    import Queue as queue
    import HTMLParser

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
ERRORS_ENCOUNTERED = False

TEXTCHARS = ''.join(map(chr, [7,8,9,10,12,13,27] + list(range(0x20, 0x100))))
DESTPATH_FILE = os.path.join(os.path.dirname(str(__file__)), "last_gallery_dest.txt")
DEST_ROOT = unicode_safe(os.getcwd())
if os.path.exists(DESTPATH_FILE):
    DEST_ROOT = unicode_safe(open(DESTPATH_FILE,"r").read().strip())

EXCEPTION_NOTICE = """An exception occurred!  We can help if you follow these steps:\n
1. Visit https://github.com/regosen/gallery_get/issues
2. Click the "New Issue" button
3. Copy the text between the lines and paste it into the issue.
(If you don't want to share the last line, the rest can still help.)"""
PARAMS = []


def safe_str(name):
    name = name.replace(":",";") # to preserve emoticons
    name = "".join(i for i in name if ord(i)<128)
    name = html_parser.unescape(name)
    return re.sub(r"[\/\\\*\?\"\<\>\|]", "", name).strip().rstrip(".")

def safe_unpack(obj, default):
    if is_str(obj):
        return (obj,safe_str(default))
    elif obj:
        return (obj[0],safe_str(obj[1]))
    else:
        return ("","")

def safe_url(parent, link):
    try:
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
    except AttributeError:
        return ""


def find_plugin(url):
    for modname in PLUGINS.keys():
        if modname == "plugin_generic":
            continue
        cur_plugin = PLUGINS[modname]
        if run_match(cur_plugin.identifier, url):
            return cur_plugin
    return PLUGINS["plugin_generic"]

def run_match(match, source, singleItem=False):
    result = []
    if not is_str(source):
        result = [source]
    elif match:
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
    elif is_iterable(result):
        # remove duplicates without affecting order (like set does)
        visited = set()
        visited_add = visited.add
        result = [x for x in result if not (x in visited or visited_add(x))]
    return result if result else []

def download_image(url, fileNameFull):
    global ERRORS_ENCOUNTERED
    try:
        urlBase, fileExtension = os.path.splitext(url.split("?")[0])
        fileName = os.path.abspath(fileNameFull)[:255] + fileExtension # full path must be 260 characters or lower
        folder = os.path.dirname(fileName)
        if not os.path.exists(folder):
            os.makedirs(folder)
        elif os.path.exists(fileName):
            print("Skipping existing file: " + url)
            return folder
        add_job(path=url, dest=folder, subtitle=fileName)
        return folder
    except:
        print("ERROR: Couldn't open URL: " + url)
        ERRORS_ENCOUNTERED = True
        return False

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
        self.override = None

    def destination_filename(self):
        indexstr = "%03d" % self.index # 001, 002, etc.

        basename = self.subtitle
        if self.override:
            basename = self.override
        elif self.plugin and self.plugin.use_filename:
            basename = unquote(os.path.basename(self.path).split("?")[0])
        elif not basename or basename == FALLBACK_TITLE:
            basename = indexstr
        elif self.index > 0:
            (basename,ext) = os.path.splitext(basename)
            basename = "%s_%s%s" % (basename, indexstr, ext)

        # copy extension (falling back on jpg)
        if not re.match(r".+\.[a-zA-Z0-9]+\Z", basename):
            ext = ".jpg"
            tokens = self.path.split("?")[0].split("/")[-1].split(".")
            if len(tokens) > 1:
                ext = "." + tokens[-1]
            basename += ext
        return os.path.join(self.dest, basename)

    def write_to_file(self, file_info, file_name):
        success = True
        try:
            if not self.data:
                self.data = file_info.read()
        except:
            success = False

        file_info.close()
        if success:
            output = open(file_name,'wb')
            output.write(self.data)
            output.close()
        return success

def start_jobs():
    global STANDBY, THREADS
    if not THREADS:
        STANDBY = True
        for i in range(multiprocessing.cpu_count()):
            t = ImgThread()
            t.start()
            THREADS.append(t)

def flush_jobs():
    global STANDBY, THREADS, ERRORS_ENCOUNTERED
    STANDBY = False
    for t in THREADS:
        t.join()
    THREADS = []

    success = not ERRORS_ENCOUNTERED
    ERRORS_ENCOUNTERED = False
    if success:
        print("Done!")
    else:
        print("Errors were encountered!  Please check messages above.")
    return success

def add_job(plugin=None, subtitle="", path="", redirect="", dest="", index=0):
    global QUEUE
    start_jobs()
    QUEUE.put(JobInfo(plugin=plugin, subtitle=subtitle, path=path, redirect=redirect, dest=dest, index=index))


class ImgThread(threading.Thread):
    """Threaded Url Grab"""

    def can_skip(self, file_name, file_info):
        if os.path.exists(file_name):
            # file already exists.  Skip if same size
            srcsize = 0
            try:
                srcsize = int(file_info.headers.get("content-length"))
            except:
                return True

            destsize = os.stat(file_name).st_size
            if srcsize == destsize:
                return True

        return False

    def copy_image(self, info):
        info.attempts += 1
        
        file_name = info.destination_filename()
        try:
            file_info = urlopen_safe(info.path)
        except:
            return False

        try:
            modtimestr = file_info.headers['last-modified']
            modtime = time.strptime(modtimestr, '%a, %d %b %Y %H:%M:%S %Z')
        except:
            modtime = None

        if self.can_skip(file_name, file_info):
            print("Skipping existing file: " + info.path)
            return True

        if info.attempts == 1:
            print("%s -> %s" % (info.path, file_name))

        if not info.write_to_file(file_info, file_name):
            return False

        if modtime is not None:
            lastmod = calendar.timegm(modtime)
            os.utime(file_name, (lastmod, lastmod))
        return os.path.getsize(file_name) > 4096

    def is_binary(self, urlresponse):
        try:
            return not 'text/html' in urlresponse.headers['Content-Type']
        except:
            return True

    def process_redirect_page(self, info, response):
        global ERRORS_ENCOUNTERED
        if self.is_binary(response):
            # looks like the redirect page is an actual image
            info.path = info.redirect
            info.data = response.read()
            info.override = info.subtitle
        elif info.plugin:
            try:
                source = response.read()
            except:
                ERRORS_ENCOUNTERED = True
                print("Error encountered reading redirect page: " + info.redirect)
                return
                
            plugin = find_plugin(info.redirect) if (info.plugin.identifier == "generic") else info.plugin
            jpegs = run_match(plugin.direct,unicode_safe(source))
            if not jpegs:
                ERRORS_ENCOUNTERED = True
                print("No links found at redirect page: " + info.redirect)
            elif len(jpegs) == 1 and not info.path:
                (info.path,info.subtitle) = safe_unpack(jpegs[0],info.subtitle)
            else:
                # redirect has multiple links, put them in their own subfolders
                for idx, path in enumerate(jpegs):
                    (path,subtitle) = safe_unpack(path,info.subtitle)
                    path = safe_url(info.redirect, path)
                    add_job(plugin=plugin, path=path, dest=os.path.join(info.dest,subtitle), index=idx+1)

    def run_internal(self):
        global QUEUE, STANDBY, MAX_ATTEMPTS, ERRORS_ENCOUNTERED
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
                    ERRORS_ENCOUNTERED = True
                    continue
                self.process_redirect_page(info, response)

            if info.path:
                info.path = safe_url(info.redirect, info.path)
                while not self.copy_image(info):
                    if info.attempts >= MAX_ATTEMPTS:
                        print("ERROR: Failed to copy %s" % info.path)
                        ERRORS_ENCOUNTERED = True
                        break
            QUEUE.task_done()

    def run(self):
        global ERRORS_ENCOUNTERED
        try:
            self.run_internal()
        except:
            print('\n' + '-'*60)
            traceback.print_exc(file=sys.stdout)
            print("Using params: %s" % sys.argv)
            print('-'*60 + '\n')
            print(EXCEPTION_NOTICE)
            ERRORS_ENCOUNTERED = True
            os._exit(1)

class GalleryGet(object):
    def __init__(self, url, folder=DEST_ROOT, useTitleAsFolder=True, allowGenericPlugin=True):
        self.url = url
        self.folder = folder.strip()
        self.title_as_folder = useTitleAsFolder
        self.allow_generic = allowGenericPlugin # DON'T USE GENERIC PLUGIN FROM REDDIT_GET
        self.plugin = find_plugin(self.url)

    def get_root_and_subtitle(self, page):
        title = run_match(self.plugin.title, page, True)
        (title, subtitle) = safe_unpack(title, "")
        title = safe_str(title)
        if not title:
            title = FALLBACK_TITLE
        root = ""
        if self.folder:
            if self.title_as_folder:
                root = self.folder
                subtitle = title
            else:
                root = os.path.join(self.folder, title)
        else:
            root = title
        return (root, subtitle)

    def queue_jobs(self, page, root, subtitle):
        global ERRORS_ENCOUNTERED
        links = []
        using_redirect = False

        if self.plugin.redirect:
            links = run_match(self.plugin.redirect, page)
            if links:
                using_redirect = True
                for idx, link in enumerate(links):
                    (link,subtitle) = safe_unpack(link, subtitle)
                    link = safe_url(self.url, link)
                    safe_makedirs(root)
                    add_job(plugin=self.plugin, redirect=link, dest=root, subtitle=subtitle, index=idx+1)

        if not using_redirect:
            links = run_match(self.plugin.direct, page)
            if len(links) == 1:
                # don't create folder for only one file
                (root, filename) = os.path.split(root)
                safe_makedirs(root)
                add_job(plugin=self.plugin, path=links[0], dest=root, subtitle=filename)
            else:
                safe_makedirs(root)
                for idx, link in enumerate(links):
                    (link,subtitle) = safe_unpack(link, subtitle)
                    link = safe_url(self.url, link)
                    add_job(plugin=self.plugin, path=link, dest=root, subtitle=subtitle, index=idx+1)
        if not links:
            if self.folder:
                ERRORS_ENCOUNTERED = True
                print("No links found at %s, please check URL and try again." % self.url)
            else:
                ERRORS_ENCOUNTERED = True
                print("No links found!  Please check URL and try again.")
            print("Sites occasionally change their markup.  Check if this tool has an update.")
            print(" - https://github.com/regosen/gallery_get")
            print(" - pip install gallery_get --update")
        return root

    def run(self):
        global QUEUE
        if not self.url:
            print("Nothing to do!")
            return False

        ### FIND MATCHING PLUGIN (BASED ON URL)
        if self.plugin == None:
            print("Couldn't access gallery page! Try saving page(s) locally and use local path instead.")
            return False
        elif (not self.allow_generic) and (self.plugin.identifier == "generic"):
            return False
        else:
            print("Using %s plugin..." % self.plugin.debugname)

        ### TRY OPENING URL
        try:
            # Don't use urlopen_text here.  We want to capture when the data is in bytes, and treat as image
            data = urlopen_safe(self.url)
            time.sleep(self.plugin.page_load_time)
            page = data.read().decode('utf-8')
        except:
            if (self.folder != DEST_ROOT) and ("." in urlparse(self.url).path):
                # this could be a direct image
                return download_image(self.url, self.folder)

            print("Skipping inaccessible link: " + self.url)
            return False

        ### BEGIN PROCESSING
        (root, subtitle) = self.get_root_and_subtitle(page)
        return self.queue_jobs(page, root, subtitle)

def run_wrapped(myurl, dest, titleAsFolder=False, cacheDest=True, flushJobs=True, allowGenericPlugin=True):
    global DEST_ROOT, PARAMS_DEBUG, ERRORS_ENCOUNTERED
    PARAMS_DEBUG = [myurl, dest, titleAsFolder]
    try:
        if cacheDest and dest:
            safeCacheDestination(dest)
            DEST_ROOT = unicode_safe(dest)
        root = GalleryGet(myurl, dest or DEST_ROOT, titleAsFolder, allowGenericPlugin).run()
        if flushJobs:
            flush_jobs()
        return root
    except:
        print('\n' + '-'*60)
        traceback.print_exc(file=sys.stdout)
        print("Using params: %s" % PARAMS_DEBUG)
        print('-'*60 + '\n')
        print(EXCEPTION_NOTICE)
        ERRORS_ENCOUNTERED = True
        return False

def run_prompted():
    global DEST_ROOT
    myurl = str_input("Input URL: ").strip()
    if not myurl:
        print("Nothing to do!")
        return False
    dest = str_input("Destination (%s): " % encode_safe(DEST_ROOT)).strip()
    return run_wrapped(myurl, dest or DEST_ROOT)

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
