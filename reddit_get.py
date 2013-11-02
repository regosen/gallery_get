# REDDIT_GET is a tool for downloading all imgur albums and pictures
# that were submitted by a given reddit user.
#
# DEPENDENCIES
# This relies on gallery_get and the imgur_album plugin.
#
# See gallery_get for more info
#
# Rego Sen
# Nov 2, 2013
#


import gallery_get, time, sys
import urllib, datetime, os, json
DEST_ROOT = gallery_get.DEST_ROOT

def reddit_url(user):
	return "http://www.reddit.com/user/%s/submitted/.json?limit=1000" % user

def download_image(url, fileNameFull):
	urlBase, fileExtension = os.path.splitext(url)
	fileName = os.path.abspath(fileNameFull)[:255] + fileExtension #full path must be 260 characters or lower
	folder = os.path.dirname(fileName)
	if not os.path.exists(folder):
		os.makedirs(folder)
	elif os.path.exists(fileName):
		print "skipping existing file: " + fileName
		return
	
	print "downloading %s -> %s" % (url, fileName)
	imgData = urllib.urlopen(url).read()
	output = open(fileName,'wb')
	output.write(imgData)
	output.close()

def run_internal(user, dest=""):
	global DEST_ROOT
	if dest:
		open(gallery_get.DESTPATH_FILE,"w").write(dest)
	elif os.path.exists(gallery_get.DESTPATH_FILE):
		dest = open(gallery_get.DESTPATH_FILE,"r").read().strip()
	DEST_ROOT = dest

	reddit_json_str = ""
	reddit_json = {}
	localpath = user + ".json"
	if os.path.exists(localpath):
		print "getting JSON data from local file (%s)" % localpath
		reddit_json_str = open(localpath,"r").read()
		reddit_json = json.loads(reddit_json_str)
	else:
		print "requesting JSON data from reddit..."
		for i in range(5):
			reddit_json_str = urllib.urlopen(reddit_url(user)).read()
			reddit_json = json.loads(reddit_json_str)
			if "data" in reddit_json:
				break
			else:
				time.sleep(2)

	if not "data" in reddit_json:
		print "ERROR getting json data after several retries!  Try saving the contents of the following to [USERNAME].json and try again."
		print reddit_url(user)
	else:
		visited_links = set()
		for post in reddit_json['data']['children']:
			url = post['data']['url']
			if not "imgur.com/" in url:
				# only supporting imgur for now
				continue
				
			if url.lower() in visited_links:
				print "Skipping already visited link: " + url
				continue
			else:
				visited_links.add(url.lower())
				
			cdate = post['data']['created']
			sdate = datetime.datetime.fromtimestamp(cdate).strftime("%Y-%m-%d")
			title = post['data']['title'].replace('/', '_').replace('\\', '_').strip()
			if title:
				title = " - " + title
				
			folder = os.path.join(dest, user, gallery_get.safestr(sdate + title))
			
			if "/i.imgur.com/" in url:
				download_image(url, folder)
			elif "/imgur.com/a/" in url:
				gallery_get.run_internal(url, folder)
			elif "/imgur.com/" in url:
				# Create direct image URL with dummy extension (otherwise it will redirect)
				# Then get correct extension from header
				# (This is way faster than opening the redirect)
				img_base = url.replace("/imgur.com/","/i.imgur.com/")
				ext = "jpg"
				file = urllib.urlopen("%s.%s" % (img_base, ext))
				real_ext = file.headers.get("content-type")[6:]
				if real_ext != "jpeg": # jpeg -> jpg
					ext = real_ext
				download_image("%s.%s" % (img_base, ext), folder)

def run_prompted():
	user = raw_input("input reddit user:").strip()
	if not user:
		print "Nothing to do!"
		sys.exit()
	new_dest = raw_input("output path (%s):" % DEST_ROOT).strip()
	run_internal(user, new_dest)

def run(user="", dest=""):
	if not user:
		run_prompted()
	else:
		run_internal(user, dest)

cur_file = os.path.basename(str(__file__))
arg_file = sys.argv[0]
if arg_file and os.path.basename(arg_file) == cur_file:
	### DIRECT LAUNCH (not import)
	if len(sys.argv) > 1:
		# use first parameter as reddit user, second (if exists) as dest
		if len(sys.argv) > 2:
			run_internal(sys.argv[1], sys.argv[2])
		else:
			run_internal(sys.argv[1])
	else:
		run_prompted()
