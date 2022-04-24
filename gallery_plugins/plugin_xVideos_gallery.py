# Plugin for gallery_get.

# Each definition can be one of the following:
# - a string
# - a regex string
# - a function that takes source as a parameter and returns an array or a string.  (You may assume that re and urllib are already imported.)
# If you comment out a parameter, it will use the default defined in __init__.py

# identifier (default = name of this plugin after "plugin_") : If there's a match, we'll attempt to download images using this plugin.
identifier = "xvideos.com/.+/photos/"

# title: parses the gallery page for a title.  This will be the folder name of the output gallery.
title = '"title":"(.+?)"'

# redirect: if the links in the gallery page go to an html instead of an image, use this to parse the gallery page.

# direct_links: if redirect is non-empty, this parses each redirect page for a single image.  Otherwise, this parses the gallery page for all images.
direct_links = r'href="(https://img-hw.xvideos-cdn.com/videos/profiles/galleries/\S+?)"'

# same_filename (default=False): if True, uses filename specified on remote link.  Otherwise, creates own filename with incremental index.
same_filename = True
