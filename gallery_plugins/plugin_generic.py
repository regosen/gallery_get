# Plugin for gallery_get.
import re

# Each definition can be one of the following:
# - a string
# - a regex string
# - a function that takes source as a parameter and returns an array or a string.  (You may assume that re and urllib are already imported.)
# If you comment out a parameter, it will use the default defined in __init__.py

# identifier (default = name of this plugin after "plugin_") : If there's a match, we'll attempt to download images using this plugin.

# title: parses the gallery page for a title.  This will be the folder name of the output gallery.
title = r'<title>(.*?)</title>'

# redirect: if the links in the gallery page go to an html instead of an image, use this to parse the gallery page.
redirect = r'href=["\']([^<]+?)["\'][^<]*?><img'

# direct_links: if redirect is non-empty, this parses each redirect page for a single image.  Otherwise, this parses the gallery page for all images.
def direct_links(source):
    matcher = re.compile(r'src=[\"\'](.+?\.jpe?g)[\"\']',re.I)
    links = matcher.findall(source)
    links = filter(lambda x: not "thumb" in x.lower(), links) # exclude thumbnails
    return links

# same_filename (default=False): if True, uses filename specified on remote link.  Otherwise, creates own filename with incremental index. 
same_filename = True
