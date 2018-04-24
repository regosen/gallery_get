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

import gallery_get
import os, time, sys, traceback
import datetime, json

from gallery_utils import *
import gallery_plugins

USER_QUERY = "https://www.reddit.com/user/%s/submitted/.json?limit=1000"
DEST_ROOT = gallery_get.DEST_ROOT
safe_makedirs(DEST_ROOT)

# To speed this up, don't craw links with pages that we know aren't galleries
NON_GALLERY_DOMAINS = [
"youtube.com",
"youtu.be",
"www.reddit.com"
]

def is_individual_imgur(url):
    if "/imgur.com/a/" in url:
        return False
    if "/imgur.com/gallery/" in url:
        return False
    return True

class RedditGet(object):
    def __init__(self, user, dest, flush_jobs=True):
        self.user = user
        self.dest = dest
        self.flush_jobs = flush_jobs

    def get_user_json(self):
        reddit_json_str = ""
        reddit_json = {}
        cache_path = self.user + ".json"
        query_url = USER_QUERY % self.user
        if os.path.exists(cache_path):
            print("Getting JSON data from local file (%s)" % cache_path)
            reddit_json_str = unicode_safe(open(cache_path,"r").read())
            reddit_json = json.loads(reddit_json_str)
        else:
            print("Requesting JSON data from reddit...")
            for i in range(5):
                try:
                    reddit_json_str = urlopen_text(query_url)
                    reddit_json = json.loads(reddit_json_str)
                except URLError:
                    break
                except Exception as e:
                    if hasattr(e, 'code') and e.code == 404:
                        break
                if "data" in reddit_json:
                    break
                else:
                    time.sleep(2) # workaround for server-side request frequency issues

        if not "data" in reddit_json:
            print("ERROR getting json data after several retries!  Does the user exist?")
            print("If so, try saving the contents of the following to %s and try again." % cache_path)
            print(query_url)
        return reddit_json

    def folder_from_post(self, data):
        sdate = datetime.datetime.fromtimestamp(data['created']).strftime("%Y-%m-%d")
        title = data['title'].replace('/', '_').replace('\\', '_').strip()
        if title:
            title = " - " + title

        return os.path.join(unicode_safe(self.dest), self.user, gallery_get.safe_str(sdate + title))

    # includes special shortcuts for skipping the redirect
    def process_reddit_post(self, url, folder):
        if "/i.reddituploads.com/" in url:
            gallery_get.download_image(url + ".jpg", folder)
        elif "/imgur.com/" in url and is_individual_imgur(url):
            # Create direct image URL with dummy extension (otherwise it will redirect)
            # Then get correct extension from header
            img_base = url.replace("/imgur.com/","/i.imgur.com/")
            ext = "jpg"
            file = urlopen_safe("%s.%s" % (img_base, ext))
            real_ext = file.headers.get("content-type")[6:]
            if real_ext != "jpeg": # jpeg -> jpg
                ext = real_ext
            gallery_get.download_image("%s.%s" % (img_base, ext), folder)
        elif "/i.imgur.com/" in url:
            gallery_get.download_image(url, folder)
        else:
            # TODO: use Queue or eventlet for launching gallery_get.run_wrapped()
            gallery_get.run_wrapped(url, folder, titleAsFolder=True, cacheDest=False, flushJobs=False, allowGenericPlugin=False)

    def run(self):
        reddit_json = self.get_user_json()

        if "data" in reddit_json:
            visited_links = set()
            num_valid_posts = 0
            for post in reddit_json['data']['children']:
                data = post['data']
                url = data['url']
                domain = urlparse(url).netloc.lower()
                if any(x in domain for x in NON_GALLERY_DOMAINS):
                    print("Skipping non-gallery link: " + url)
                    continue
                elif url.lower() in visited_links:
                    print("Skipping already visited link: " + url)
                    continue
                else:
                    visited_links.add(url.lower())

                self.process_reddit_post(url, self.folder_from_post(data))
        if self.flush_jobs:
            gallery_get.flush_jobs()

def run_wrapped(user, dest="", flush_jobs=True):
    global DEST_ROOT
    try:
        if dest:
            gallery_get.safeCacheDestination(dest)
            DEST_ROOT = unicode_safe(dest)
        RedditGet(user, dest or DEST_ROOT, flush_jobs).run()
    except:
        print('\n' + '-'*60)
        traceback.print_exc(file=sys.stdout)
        print("Using params: [%s, %s]" % (user, dest))
        print('-'*60 + '\n')
        print(gallery_get.EXCEPTION_NOTICE)
    return os.path.join(DEST_ROOT, user)

def run_prompted():
    user = str_input("Input reddit user: ").strip()
    if not user:
        print("Nothing to do!")
        sys.exit()
    dest = str_input("Destination (%s): " % encode_safe(DEST_ROOT)).strip()
    if dest:
        gallery_get.safeCacheDestination(dest)
    RedditGet(user, dest or DEST_ROOT).run()

def run(user="", dest=""):
    if not user:
        run_prompted()
    else:
        run_wrapped(user, dest)

cur_file = os.path.basename(str(__file__))
arg_file = sys.argv[0]
if arg_file and os.path.basename(arg_file) == cur_file:
    ### DIRECT LAUNCH (not import)
    if len(sys.argv) > 1:
        # use first parameter as reddit user, second (if exists) as dest
        if len(sys.argv) > 2:
            run_wrapped(sys.argv[1], sys.argv[2])
        else:
            run_wrapped(sys.argv[1])
    else:
        run_prompted()
