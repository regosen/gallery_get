# Plugin for gallery_get.
import re
import sys
# Each definition can be one of the following:
# - a string
# - a regex string
# - a function that takes source as a parameter and returns an array or a string.  (You may assume that re and urllib are already imported.)
# If you comment out a parameter, it will use the default defined in __init__.py

# identifier (default = name of this plugin after "plugin_") : If there's a match, we'll attempt to download images using this plugin.
identifier = 'fuskator.com'

# title: parses the gallery page for a title.  This will be the folder name of the output gallery.
def title(source):
    matcher = re.compile(r'<head><title>(.*?)</title>', re.DOTALL)
    gallery = matcher.findall(source)
    return gallery[0].strip()

# redirect: if the links in the gallery page go to an html instead of an image, use this to parse the gallery page.
def redirect(source):
    protocol = re.findall(r'link href=\"(http[s]?:\/\/)', source)[0]
    # Are we working with a thumbnails page or the full size image page
    thumbs_page = len(re.findall(r'<a class=\"navlink\" href=\"(.*?)\">View full images</a>', source))
    if bool(thumbs_page):
        links = re.findall(r'<div class=\'pic\'><a href=\'\/\/(.*?)\' rel=\'group\'>', source)
    else:
        links = re.findall(r'<img class=\'full\' .*? src=\'\/\/(.*?)\' ondragstart=.*?\/>', source)
    links = map(lambda x: protocol + x, links)
    links = set(links)  # Ensure we don't have any duplicates
    return links

# direct_links: if redirect is non-empty, this parses each redirect page for a single image.  Otherwise, this parses the gallery page for all images.
direct_links = r'http[s]?:\/\/.*?\/large\/.*?\.jpg'

# same_filename (default=False): if True, uses filename specified on remote link.  Otherwise, creates own filename with incremental index.
same_filename = True
