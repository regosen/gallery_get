# Initialization file for gallery_get
#
# Rego Sen
# Aug 22, 2013
#

DEFAULT_TITLE = r'<title>(.*?)</title>'
DEFAULT_REDIRECT = "" # assumes all links are direct links
DEFAULT_DIRECT_LINKS = r'src=[\"\'](.+?\.jpe?g)[\"\']'
DEFAULT_USE_FILENAME = False
DEFAULT_PAGE_LOAD_TIME = 0

import os,sys
PLUGINS = {}
DEFAULT_PLUGIN = None
FALLBACK_TITLE = "Untitled Gallery"

class Plugin(object):
    def __init__(self, debugname, identifier):
        self.debugname = debugname
        self.identifier = identifier
        self.redirect = DEFAULT_REDIRECT
        self.direct = DEFAULT_DIRECT_LINKS
        self.title = DEFAULT_TITLE
        self.use_filename = DEFAULT_USE_FILENAME
        self.page_load_time = DEFAULT_PAGE_LOAD_TIME

def register_plugin(mod, modname, debugname):
    mod_locals = dir(mod)
    if not 'identifier' in mod_locals:
        mod.identifier = debugname
    if not modname in PLUGINS:
        PLUGINS[modname] = Plugin(debugname, mod.identifier)
    if 'title' in mod_locals:
        PLUGINS[modname].title = mod.title 
    if 'redirect' in mod_locals:
        PLUGINS[modname].redirect = mod.redirect 
    if 'direct_links' in mod_locals:
        PLUGINS[modname].direct = mod.direct_links 
    if 'same_filename' in mod_locals:
        PLUGINS[modname].use_filename = mod.same_filename 
    if 'page_load_time' in mod_locals:
        PLUGINS[modname].page_load_time = mod.page_load_time 

# import all python files starting with "plugin_"
directory = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, directory)
plugin_prefix = "plugin_"
for file in os.listdir(directory):
    filelower = file.lower()
    if filelower.startswith(plugin_prefix) and filelower.endswith(".py"):
        f, e = os.path.splitext(file)
        try:
            mod = __import__(f)
            name = mod.__name__
            debugname = name[len(plugin_prefix):] # text after prefix
            register_plugin(mod, name, debugname)
            
        except ImportError:
            print("Gallery: failed to import")
            print(f, ":", sys.exc_value)
