# Plugin for gallery_get.
import re

# Each definition can be one of the following:
# - a string to match
# - a regex string to match
# - a function that takes source as a parameter and returns an array or a single match.  (You may assume that re and urllib are already imported.)
# If you comment out a parameter, it will use the default defined in __init__.py

# identifier (default = name of this plugin after "plugin_") : If there's a match, we'll attempt to download images using this plugin.
identifier = "vidble.com"

# title: parses the gallery page for a title.  This will be the folder name of the output gallery.
title = r'<title>"(.*?)</title>"'

# redirect: if the links in the gallery page go to an html instead of an image, use this to parse the gallery page.

# direct_links: if redirect is non-empty, this parses each redirect page for a single image.  Otherwise, this parses the gallery page for all images.
# * if using regex, you can have two matches: the first will be the link and the second will be the basename of the file.
#   if the matches need to be reversed, use named groups "link" and "basename"

def direct_links(source):
    links = re.findall('img src=[\"\'](.+?\.jpe?g)[\"\']',source)
    links = filter(lambda x: "/assets/" not in x, links)
    return map(lambda x: 'http://vidble.com' + x, links)

# same_filename (default=False): if True, uses same filename from remote link.  Otherwise, creates own filename with incremental index (or uses subtitle). 