# Plugin for gallery_get.
import re
from gallery_utils import urlopen_text

# Each definition can be one of the following:
# - a string
# - a regex string
# - a function that takes source as a parameter and returns an array or a string.  (You may assume that re and urllib are already imported.)
# If you comment out a parameter, it will use the default defined in __init__.py

# identifier (default = name of this plugin after "plugin_") : If there's a match, we'll attempt to download images using this plugin.

# title: parses the gallery page for a title.  This will be the folder name of the output gallery.
title = r'<title>(.*?) - xHamster.com</title>'

# redirect: if the links in the gallery page go to an html instead of an image, use this to parse the gallery page.
def redirect(source):
    redirects = re.findall(r'property="og:url" content="(\S+?)"', source)
    indexed_source = source
    while True:
        next_url = re.findall(r'rel="next" href="(\S+?)"', indexed_source)
        if next_url:
          indexed_page = next_url[0]
          redirects.append(indexed_page)
          print("Crawling " + indexed_page)
          indexed_source = urlopen_text(indexed_page)
        else:
          break
    return redirects

# direct_links: if redirect is non-empty, this parses each redirect page for a single image.  Otherwise, this parses the gallery page for all images.
def direct_links(source):
    links = re.findall(r'"imageURL":"(\S+?)"',source)
    return map(lambda x: x.replace("\/", "/"), links)

# same_filename (default=False): if True, uses filename specified on remote link.  Otherwise, creates own filename with incremental index. 
same_filename = True
