# Plugin for gallery_get.
import re
from gallery_utils import *

# Each definition can be one of the following:
# - a string
# - a regex string
# - a function that takes source as a parameter and returns an array or a string.
# If you comment out a parameter, it will use the default defined in __init__.py

# identifier (default = name of this plugin after "plugin_") : If there's a match, we'll attempt to download images using this plugin.

# title: parses the gallery page for a title.  This will be the folder name of the output gallery.
title = r'<title>(.+?)</title>'

# redirect: if the links in the gallery page go to an html instead of an image, use this to parse the gallery page.
def redirect(source):
    redirects = []
    cur_url = re.findall(r'href=\'(.+?)\'\>', source)[0].split("?")[0]
    index = 0
    while True:
        indexed_page = cur_url + "?page=%d" % index
        print("Crawling " + indexed_page)
        indexed_source = urlopen_text(indexed_page)
        links = re.findall('href=[\"\'](/photo/.+)[\"\']',indexed_source)
        if links:
            redirects += map(lambda x: 'http://www.imagefap.com' + x, links)
            index += 1
        else:
            break
    return redirects

# direct_links: if redirect is non-empty, this parses each redirect page for a single image.  Otherwise, this parses the gallery page for all images.
direct_links = r'name="mainPhoto".+?(http://x.imagefapusercontent.com/.+?\.(jpe?g?|png|gif))'

# same_filename (default=False): if True, uses filename specified on remote link.  Otherwise, creates own filename with incremental index. 
same_filename = True
