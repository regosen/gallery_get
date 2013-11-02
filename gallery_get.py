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


import os,time,sys
import urllib
import re
import Queue
import threading
import gallery_plugins
import HTMLParser
from urlparse import urlparse
html_parser = HTMLParser.HTMLParser()

# some galleries reject requests if they're not coming from a browser- this is to get past that.
class BrowserFaker(urllib.FancyURLopener):
    version = "Mozilla/5.0"
urllib._urlopener = BrowserFaker()

QUEUE = Queue.Queue()
JOBS_PENDING = True
INDEX = 1
MAX_ATTEMPTS = 10

PLUGIN = gallery_plugins.PLUGINS["plugin_generic"]
DESTPATH_FILE = "last_gallery_dest.txt"
DEST_ROOT = os.getcwd()

TEXTCHARS = ''.join(map(chr, [7,8,9,10,12,13,27] + range(0x20, 0x100)))
def is_binary(datastring):
	return bool(datastring.translate(None, TEXTCHARS))

def safestr(name):
	name = name.replace(":",";") # to preserve emoticons
	name = html_parser.unescape(name)
	name = "".join(i for i in name if ord(i)<128)
	return re.sub(r"[\/\\\*\?\"\<\>\|]", "", name).strip()
	
def is_str(obj):
	return isinstance(obj, basestring)

def safe_unpack(obj, default):
	return (obj,safestr(default)) if is_str(obj) else (obj[0],safestr(obj[1]))
	
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
		return result if is_str(result) else result[0] if result else ""
	else:
		return [result] if is_str(result) else list(set(result))

class JobInfo(object):
	def __init__(self, subtitle="", path="", redirect="", dest=""):
		global INDEX
		self.index = INDEX
		INDEX += 1
		self.redirect = redirect
		self.path = path
		self.subtitle = subtitle
		self.attempts = 0
		self.dest = dest
		self.data = None



def safeurl(parent, link):
	if not link.lower().startswith("http"):
		if link.startswith("/"):
			domain = '{uri.scheme}://{uri.netloc}/'.format(uri=urlparse(parent))
			link = domain + link
		else:
			link = os.path.dirname(parent) + "/" + link
	return link.replace("&amp;","&")

class ImgThread(threading.Thread):
	"""Threaded Url Grab"""
	
	def copyImage(self, info):
		info.attempts += 1
		indexstr = "%03d" % info.index # 001, 002, etc.

		basename = info.subtitle
		if PLUGIN.useFilename:
			basename = os.path.basename(info.path).split("?")[0]
		else:
			if not basename or basename == gallery_plugins.FALLBACK_TITLE:
				basename = indexstr
		
		if not re.match(r".+\.[a-zA-Z0-9]+", basename):
			# preserve extension (or assume jpg)
			ext = ".jpg"
			tokens = info.path.split("?")[0].split(".")
			if len(tokens) > 1:
				ext = "." + tokens[-1]
			basename += ext
				
		fileName = os.path.join(info.dest, basename)
		(basename,ext) = fileName.rsplit(".",1)
		fileNameIndexed = "%s_001.%s" % (basename,ext)
		
		if info.dest and not os.path.exists(info.dest):
			os.makedirs(info.dest)
		else:
			existingFile = fileName if os.path.exists(fileName) else fileNameIndexed if os.path.exists(fileNameIndexed) else ""
			if existingFile:
				# file already exists.  Skip if same size, add index otherwise.
				srcsize = 0
				try:
					file = urllib.urlopen(info.path)
					srcsize = int(file.headers.get("content-length"))
					file.close()
				except:
					print "Skipping " + existingFile + " (couldn't compare file size)"
					return True
				
				destsize = os.stat(existingFile).st_size
				if srcsize == destsize:
					print "Skipping " + existingFile
					return True
			
				if not os.path.exists(fileNameIndexed):
					os.rename(fileName, fileNameIndexed)
				fileName = "%s_%s.%s" % (basename,indexstr,ext)
		
		if info.attempts == 1:
			print "%s -> %s" % (info.path, fileName)
		else:
			print "%s -> %s (Attempt %d)" % (info.path, fileName, info.attempts)
		try:
			if not info.data:
				info.data = urllib.urlopen(info.path).read()
			output = open(fileName,'wb')
			output.write(info.data)
			output.close()
			return os.path.getsize(fileName) > 4096
		except:
			# don't bother printing anything, will display next attempt
			return False
	
	def run(self):
		global QUEUE, JOBS_PENDING, MAX_ATTEMPTS, INDEX
		while JOBS_PENDING or not QUEUE.empty():
			if QUEUE.empty():
				time.sleep(1)
				continue
			info = QUEUE.get()
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
						QUEUE.put(JobInfo(path=j, dest=os.path.join(info.dest,subtitle)))
			if info.path:
				info.path = safeurl(info.redirect, info.path)
				while not self.copyImage(info):
					if info.attempts >= MAX_ATTEMPTS:
						print "ERROR: Failed to copy " + info.path
						break
				
		#signals to queue job is done
		if INDEX > 0:
			QUEUE.task_done()

def run_internal(myurl,folder=DEST_ROOT,usetitleasfolder=True):
	global JOBS_PENDING, PLUGIN, INDEX
	if not myurl:
		print "Nothing to do!"
		return
	
	JOBS_PENDING = True
	INDEX = 0

	page = urllib.urlopen(myurl).read()
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

	### START THREADS
	t = ImgThread()
	t.start()

	### QUEUE JOBS FOR OPENING LINKS
	links = []
	# TODO: DRY
	if PLUGIN.redirect:
		links = run_match(PLUGIN.redirect, page)
		for link in links:
			(link,subtitle) = safe_unpack(link, subtitle)
			link = safeurl(myurl, link)
			QUEUE.put(JobInfo(redirect=link, dest=root, subtitle=subtitle))
	else:
		links = run_match(PLUGIN.direct, page)
		for link in links:
			(link,subtitle) = safe_unpack(link, subtitle)
			link = safeurl(myurl, link)
			QUEUE.put(JobInfo(path=link, dest=root, subtitle=subtitle))
	if not links:
		if folder:
			print "No links found at %s  Check regex." % myurl
		else:
			print "No links found!  Check regex."

	JOBS_PENDING = False
	t.join()


def run_prompted():
	global DEST_ROOT
	myurl = raw_input("input url:").strip()
	new_dest = raw_input("output path (%s):" % DEST_ROOT).strip()
	if new_dest:
		open(DESTPATH_FILE,"w").write(new_dest)
		DEST_ROOT = new_dest
	run_internal(myurl, DEST_ROOT, False)


def run(myurl="", dest=""):
	if not myurl:
		run_prompted()
	else:
		if dest:
			open(DESTPATH_FILE,"w").write(dest)
		elif os.path.exists(DESTPATH_FILE):
			dest = open(DESTPATH_FILE,"r").read().strip()
		run_internal(myurl, dest, False)


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
			open(DESTPATH_FILE,"w").write(DEST_ROOT)
		run_internal(sys.argv[1], DEST_ROOT, False)
	else:
		run_prompted()

