# Plugin for gallery_get.
import re
from gallery_utils import *

# Each definition can be one of the following:
# - a string
# - a regex string
# - a function that takes source as a parameter and returns an array or a string.  (You may assume that re and urllib are already imported.)
# If you comment out a parameter, it will use the default defined in __init__.py

# identifier (default = name of this plugin after "plugin_") : If there's a match, we'll attempt to download images using this plugin.

# title: parses the gallery page for a title.  This will be the folder name of the output gallery.

# redirect: if the links in the gallery page go to an html instead of an image, use this to parse the gallery page.
def redirect(source):
    redirects = []
    base_url = "http://shimmie.shishnet.org"
    cur_url = re.findall(r'href="(.+?)"\>Random</a>', source)[0].rsplit("/",1)[0]
    index = 0
    while True:
        indexed_page = "%s%s/%s" % (base_url, cur_url, index)
        print("Crawling " + indexed_page)
        try:
          indexed_source = urlopen_text(indexed_page)
          links = re.findall("href='(.+?)' class='thumb", indexed_source)
          if links:
              redirects += map(lambda x: base_url + x, links)
              index += 1
          else:
              break
        except:
          break
    return redirects

# direct_links: if redirect is non-empty, this parses each redirect page for a single image.  Otherwise, this parses the gallery page for all images.
direct_links = r"name='ubb_full-img' value='\[img\](.+?)\[/img\]'"


# same_filename (default=False): if True, uses filename specified on remote link.  Otherwise, creates own filename with incremental index. 
same_filename = True