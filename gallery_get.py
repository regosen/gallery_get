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
import urllib
import re
import Queue
import threading
import gallery_plugins
import HTMLParser
import multiprocessing
from urlparse import urlparse
html_parser = HTMLParser.HTMLParser()

# some galleries reject requests if they're not coming from a browser- this is to get past that.
class BrowserFaker(urllib.FancyURLopener):
    version = "Mozilla/5.0"
urllib._urlopener = BrowserFaker()

QUEUE = Queue.Queue()
STANDBY = False
THREADS = []
MAX_ATTEMPTS = 10

PLUGIN = gallery_plugins.PLUGINS["plugin_generic"]
TEXTCHARS = ''.join(map(chr, [7,8,9,10,12,13,27] + range(0x20, 0x100)))
DESTPATH_FILE = os.path.join(os.path.dirname(str(__file__)), "last_gallery_dest.txt")
DEST_ROOT = os.getcwd()

EXCEPTION_NOTICE = """An exception occurred!  We can help if you follow these steps:\n
1. Visit https://github.com/regosen/gallery_get/issues
2. Click the "New Issue" button
3. Copy the text between the lines and paste it into the issue.
(If you don't want to share the last line, the rest can still help.)"""
PARAMS = []

def is_binary(datastring):
    return bool(datastring.translate(None, TEXTCHARS))

def safestr(name):
    name = name.replace(":",";") # to preserve emoticons
    name = "".join(i for i in name if ord(i)<128)
    name = html_parser.unescape(name)
    return re.sub(r"[\/\\\*\?\"\<\>\|]", "", name).strip().rstrip(".")
    
def is_str(obj):
    return isinstance(obj, basestring)

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
    elif result:
        result = [result] if is_str(result) else list(set(result))
    return result if result else []

def safeurl(parent, link):
    if not link.lower().startswith("http"):
        domain = '{uri.scheme}://{uri.netloc}/'.format(uri=urlparse(parent))
        if link.startswith("/") or domain.strip('/').lower() == parent.strip('/').lower():
            link = domain + link
        else:
            link = os.path.dirname(parent) + "/" + link
    return link.replace("&amp;","&")


class JobInfo(object):
    def __init__(self, subtitle="", path="", redirect="", dest="", index=0):
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

def add_job(subtitle="", path="", redirect="", dest="", index=0):
    global QUEUE
    start_jobs()
    QUEUE.put(JobInfo(subtitle=subtitle,path=path, redirect=redirect, dest=dest, index=index))
    


class ImgThread(threading.Thread):
    """Threaded Url Grab"""
    
    def copyImage(self, info):
        info.attempts += 1
        indexstr = "%03d" % info.index # 001, 002, etc.

        basename = info.subtitle
        if PLUGIN.useFilename:
            basename = os.path.basename(info.path).split("?")[0]
        elif not basename or basename == gallery_plugins.FALLBACK_TITLE:
            basename = indexstr
        elif info.index > 0:
            (basename,ext) = os.path.splitext(basename)
            basename = "%s_%s%s" % (basename, indexstr, ext)
        
        # copy extension (falling back on jpg)
        if not re.match(r".+\.[a-zA-Z0-9]+\Z", basename):
            ext = ".jpg"
            tokens = info.path.split("?")[0].split(".")
            if len(tokens) > 1:
                ext = "." + tokens[-1]
            basename += ext
                
        fileName = os.path.join(info.dest, basename)
        if os.path.exists(fileName):
            # file already exists.  Skip if same size
            srcsize = 0
            try:
                file = urllib.urlopen(info.path)
                srcsize = int(file.headers.get("content-length"))
                file.close()
            except:
                print "Skipping " + fileName + " (couldn't compare file size)"
                return True
            
            destsize = os.stat(fileName).st_size
            if srcsize == destsize:
                print "Skipping " + fileName
                return True
    
        if info.attempts == 1:
            print "%s -> %s" % (info.path, fileName)
        else:
            print "%s -> %s (Attempt %d)" % (info.path, fileName, info.attempts)
        try:
            if not info.data:
                info.data = urllib.urlopen(info.path).read()
        except:
            # don't bother printing anything, will display next attempt
            return False
        output = open(fileName,'wb')
        output.write(info.data)
        output.close()
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
                rpage = urllib.urlopen(info.redirect).read()
                jpegs = run_match(PLUGIN.direct,rpage)
                if not jpegs:
                    if is_binary(rpage[:1024]):
                        # looks like the redirect page is an actual image
                        info.path = info.redirect
                        info.data = rpage
                    else:
                        print "No links found at redirect page!  Check regex.  Redirect URL:"
                        print info.redirect
                elif len(jpegs) == 1 and not info.path:
                    (info.path,info.subtitle) = safe_unpack(jpegs[0],info.subtitle)
                else:
                    # redirect has multiple links, put them in their own subfolders
                    for j in jpegs:
                        (j,subtitle) = safe_unpack(j,info.subtitle)
                        j = safeurl(info.redirect, j)
                        add_job(path=j, dest=os.path.join(info.dest,subtitle))
            if info.path:
                info.path = safeurl(info.redirect, info.path)
                while not self.copyImage(info):
                    if info.attempts >= MAX_ATTEMPTS:
                        print "ERROR: Failed to copy " + info.path
                        break
            QUEUE.task_done()
    
    def run(self):
        try:
            self.run_internal()
        except:
            print '\n' + '-'*60
            traceback.print_exc(file=sys.stdout)
            print "Using params: %s" % PARAMS_DEBUG
            print '-'*60 + '\n'
            print EXCEPTION_NOTICE
            os._exit(1)

def run_internal(myurl,folder=DEST_ROOT,usetitleasfolder=True):
    global PLUGIN, QUEUE
    if not myurl:
        print "Nothing to do!"
        return

    try:
        page = urllib.urlopen(myurl).read()
    except:
        print "ERROR: Couldn't open URL: " + myurl
        return
    folder = folder.strip()

    ### FIND MATCHING PLUGIN
    for modname in gallery_plugins.PLUGINS.keys():
        if modname == "plugin_generic":
            continue
        cur_plugin = gallery_plugins.PLUGINS[modname]
        if run_match(cur_plugin.identifier, page):
            print "Using " + modname
            PLUGIN = cur_plugin
            break
    if PLUGIN.identifier == "generic":
        if "access denied" in page.lower():
            print "Access was denied! Try saving the gallery page to a local file and use local path instead."
            sys.exit(0)
        else:
            print "Using generic plugin."

    ### CREATE FOLDER FROM PAGE TITLE
    title = run_match(PLUGIN.title, page, True)
    (title, subtitle) = safe_unpack(title, "")
    title = safestr(title)
    if not title:
        title = gallery_plugins.FALLBACK_TITLE
    root = ""
    if folder:
        if usetitleasfolder:
            root = folder
            subtitle = title
        else:
            root = os.path.join(folder, title)
    else:
        root = title

    
    ### QUEUE JOBS FOR OPENING LINKS
    links = []
    # TODO: DRY
    if PLUGIN.redirect:
        links = run_match(PLUGIN.redirect, page)
        for link in links:
            (link,subtitle) = safe_unpack(link, subtitle)
            link = safeurl(myurl, link)
            if not os.path.exists(root):
                os.makedirs(root)
            add_job(redirect=link, dest=root, subtitle=subtitle)
    else:
        links = run_match(PLUGIN.direct, page)
        if len(links) == 1:
            # don't create folder for only one file
            (root, filename) = os.path.split(root)
            if not os.path.exists(root):
                os.makedirs(root)
            add_job(path=links[0], dest=root, subtitle=filename)
        else:
            idx = 1
            if not os.path.exists(root):
                os.makedirs(root)
            for link in links:
                (link,subtitle) = safe_unpack(link, subtitle)
                link = safeurl(myurl, link)
                add_job(path=link, dest=root, subtitle=subtitle, index=idx)
                idx += 1
    if not links:
        if folder:
            print "No links found at %s, plugin may need updating." % myurl
        else:
            print "No links found!  Plugin may need updating."
        print "Sites occasionally change their markup.  Check if this tool has an update."
        print " - https://github.com/regosen/gallery_get"
        print " - pip install gallery_get --update"


def run_wrapped(myurl, dest, titleAsFolder=False, cacheDest=True, flushJobs=True):
    global DEST_ROOT, PARAMS_DEBUG
    PARAMS_DEBUG = [myurl, dest, titleAsFolder]
    try:
        if cacheDest:
            if dest:
                safeCacheDestination(dest)
            elif os.path.exists(DESTPATH_FILE):
                dest = open(DESTPATH_FILE,"r").read().strip()
            DEST_ROOT = dest
        run_internal(myurl, dest, titleAsFolder)
        if flushJobs:
            flush_jobs()
    except:
        print '\n' + '-'*60
        traceback.print_exc(file=sys.stdout)
        print "Using params: %s" % PARAMS_DEBUG
        print '-'*60 + '\n'
        print EXCEPTION_NOTICE
        return False
    return True

def run_prompted():
    global DEST_ROOT
    myurl = raw_input("Input URL: ").strip()
    new_dest = raw_input("Destination (%s): " % DEST_ROOT).strip()
    if new_dest:
        run_wrapped(myurl, new_dest)
    else:
        run_wrapped(myurl, DEST_ROOT)


def run(myurl="", dest=""):
    if not myurl:
        run_prompted()
    else:
        run_wrapped(myurl, dest)

def safeCacheDestination(dest):
	try:
		open(DESTPATH_FILE,"w").write(dest)
	except:
		pass

cur_file = os.path.basename(str(__file__))
arg_file = sys.argv[0]
if os.path.exists(DESTPATH_FILE):
    DEST_ROOT = open(DESTPATH_FILE,"r").read().strip()
    
if arg_file and os.path.basename(arg_file) == cur_file:
    ### DIRECT LAUNCH (not import)
    if len(sys.argv) > 1:
        # use first parameter as url, second (if exists) as dest
        if len(sys.argv) > 2:
            DEST_ROOT = sys.argv[2]
            safeCacheDestination(DEST_ROOT)
        run_wrapped(sys.argv[1], DEST_ROOT)
    else:
        run_prompted()

