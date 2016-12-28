# Plugin for gallery_get.
import re

# Each definition can be one of the following:
# - a string to match
# - a regex string to match
# - a function that takes source as a parameter and returns an array or a single match.  (You may assume that re and urllib are already imported.)
# If you comment out a parameter, it will use the default defined in __init__.py

# identifier (default = name of this plugin after "plugin_") : If there's a match, we'll attempt to download images using this plugin.
identifier = "imgur.com/a/"

# title: parses the gallery page for a title.  This will be the folder name of the output gallery.
title = r'property="og:title" content="(.*?)"'

# redirect: if the links in the gallery page go to an html instead of an image, use this to parse the gallery page.
def redirect(source):
  if "post-loadall" in source:
    # not all images are available on this page, redirect to grid version instead
    regex = r'class="post-gridview-link"[^<>]+?href="(.+?)"'
    return re.findall(regex, source, re.I)
  else:
    return None

# direct_links: if redirect is non-empty, this parses each redirect page for a single image.  Otherwise, this parses the gallery page for all images.
# * if using regex, you can have two matches: the first will be the link and the second will be the basename of the file.
#   if the matches need to be reversed, use named groups "link" and "basename"
def direct_links(source):
    matcher = re.compile(r'"images":\[(.+?)\]}',re.I)
    sections = matcher.findall(source)
    links = []
    for section in sections:
      array = eval("[" + section.replace("null",'""').replace("[","").replace("]","").replace("true","True").replace("false","False") + "]")
      links += map(lambda x: "http://i.imgur.com/" + x["hash"] + ".jpg", array)
    return links

# same_filename (default=False): if True, uses same filename from remote link.  Otherwise, creates own filename with incremental index (or uses subtitle). 
