import gallery_get, time, sys
import urllib, datetime, os, json

if len(sys.argv) > 1:
	# use first parameter as reddit user, second (if exists) as dest
	if len(sys.argv) > 2:
		gallery_get.dest_root = sys.argv[2]
		open(gallery_get.DESTPATH_FILE,"w").write(gallery_get.dest_root)
	user = sys.argv[1]
else:
	user = raw_input("input reddit user:").strip()
	if not user:
		print "Nothing to do!"
		sys.exit()
	new_dest = raw_input("output path (%s):" % gallery_get.dest_root).strip()
	if new_dest:
		open(gallery_get.DESTPATH_FILE,"w").write(new_dest)
		gallery_get.dest_root = new_dest
reddit_url = r"http://www.reddit.com/user/%s/submitted/.json?limit=1000" % user

def download_jpeg(url, fileNameFull):
	fileName = os.path.abspath(fileNameFull)[:256] + ".jpg" #full path must be 260 characters or lower, including ".jpg"
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
		reddit_json_str = urllib.urlopen(reddit_url).read()
		reddit_json = json.loads(reddit_json_str)
		if "data" in reddit_json:
			break
		else:
			time.sleep(2)

if not "data" in reddit_json:
	print "ERROR getting json data after several retries!  Try saving the contents of the following to [USERNAME].json and try again."
	print reddit_url
else:
	for post in reddit_json['data']['children']:
		url = post['data']['url']
		cdate = post['data']['created']
		sdate = datetime.datetime.fromtimestamp(cdate).strftime("%Y-%m-%d")
		title = post['data']['title'].replace('/', '_').replace('\\', '_').strip()
		if title:
			title = " - " + title
		folder = os.path.join(gallery_get.dest_root, user, gallery_get.safestr(sdate + title))
		
		if "/a/" in url:
			gallery_get.run(url, folder)
		elif "/i.imgur.com/" in url:
			download_jpeg(url, folder)
		elif "/imgur.com/" in url:
			download_jpeg(url.replace("/imgur.com/","/i.imgur.com/") + ".jpg", folder)
