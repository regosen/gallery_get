# Initialization file for gallery_get
#
# Rego Sen
# Aug 22, 2013
#

DEFAULT_TITLE = r'<title>(.*?)</title>'
DEFAULT_REDIRECT = "" # assumes all links are direct links
DEFAULT_DIRECT_LINKS = r'src=[\"\'](.+?\.jpe?g)[\"\']'
DEFAULT_USE_FILENAME = False

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
        self.useFilename = DEFAULT_USE_FILENAME

def register_plugin(modname, debugname, identifier):
    if not modname in PLUGINS:
        PLUGINS[modname] = Plugin(debugname, identifier)

def register_title(modname, title):
    PLUGINS[modname].title = title
    
def register_redirect(modname, redirect):
    PLUGINS[modname].redirect = redirect
    
def register_links(modname, direct):
    PLUGINS[modname].direct = direct
    
def register_usefile(modname, useFile):
    PLUGINS[modname].useFilename = useFile

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
            locals = dir(mod)
            name = mod.__name__
            debugname = name[len(plugin_prefix):] # text after prefix
            if not 'identifier' in locals:
                mod.identifier = debugname
            register_plugin(name, debugname, mod.identifier)
            if 'title' in locals: register_title(name, mod.title)
            if 'redirect' in locals: register_redirect(name, mod.redirect)
            if 'direct_links' in locals: register_links(name, mod.direct_links)
            if 'same_filename' in locals: register_usefile(name, mod.same_filename)
        except ImportError:
            print("Gallery: failed to import")
            print(f, ":", sys.exc_value)
