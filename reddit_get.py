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

DEST_ROOT = gallery_get.DEST_ROOT

def reddit_url(user):
    return "http://www.reddit.com/user/%s/submitted/.json?limit=1000" % user

def is_individual_imgur(url):
    if "/imgur.com/a/" in url:
        return False
    if "/imgur.com/gallery/" in url:
        return False
    return True

# TODO: use queue or eventlet for launching gallery_get.run_wrapped()
def run_internal(user, dest):
    reddit_json_str = ""
    reddit_json = {}
    localpath = user + ".json"
    if os.path.exists(localpath):
        print("Getting JSON data from local file (%s)" % localpath)
        reddit_json_str = open(localpath,"r").read().decode('utf-8')
        reddit_json = json.loads(reddit_json_str)
    else:
        print("Requesting JSON data from reddit...")
        for i in range(5):
            try:
                reddit_json_str = urlopen_safe(reddit_url(user)).read().decode('utf-8')
                reddit_json = json.loads(reddit_json_str)
            except Exception as e:
                if e.code == 404:
                    break
            if "data" in reddit_json:
                break
            else:
                time.sleep(2) # workaround for server-side request frequency issues

    if not "data" in reddit_json:
        print("ERROR getting json data after several retries!  Does the user exist?")
        print("If so, try saving the contents of the following to %s and try again." % localpath)
        print(reddit_url(user))
    else:
        visited_links = set()
        num_valid_posts = 0
        for post in reddit_json['data']['children']:
            url = post['data']['url']

            if url.lower() in visited_links:
                print("Skipping already visited link: " + url)
                continue
            else:
                visited_links.add(url.lower())

            cdate = post['data']['created']
            sdate = datetime.datetime.fromtimestamp(cdate).strftime("%Y-%m-%d")
            title = post['data']['title'].replace('/', '_').replace('\\', '_').strip()
            if title:
                title = " - " + title

            folder = os.path.join(gallery_get.unicode_safe(dest), user, gallery_get.safestr(sdate + title))
            
            # special shortcuts for skipping the redirect
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
                gallery_get.run_wrapped(url, folder, titleAsFolder=True, cacheDest=False, flushJobs=False, allowGenericPlugin=False)

        gallery_get.flush_jobs()
        print("Done!")

def run_wrapped(user, dest=""):
    global DEST_ROOT
    try:
        if dest:
            gallery_get.safeCacheDestination(dest)
        elif os.path.exists(gallery_get.DESTPATH_FILE):
            dest = open(gallery_get.DESTPATH_FILE,"r").read().strip()
        DEST_ROOT = gallery_get.unicode_safe(dest)
        run_internal(user, dest)
    except:
        print('\n' + '-'*60)
        traceback.print_exc(file=sys.stdout)
        print("Using params: [%s, %s]" % (user, dest))
        print('-'*60 + '\n')
        print(gallery_get.EXCEPTION_NOTICE)

def run_prompted():
    user = str_input("Input reddit user: ").strip()
    if not user:
        print("Nothing to do!")
        sys.exit()
    new_dest = str_input("Destination (%s): " % gallery_get.encode_safe(DEST_ROOT)).strip()
    run_wrapped(user, new_dest)

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
