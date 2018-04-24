import os

# Python 3 imports that throw in Python 2
try:
    from urllib.request import Request, urlopen, URLError
    from urllib.parse import urlparse, unquote
except ImportError:
    # This is Python 2
    from urllib2 import Request, urlopen, URLError
    from urlparse import urlparse
    from urllib import unquote

# Python 2 types that throw in Python 3
try:
    str_input = raw_input
    str_type = basestring
except:
    # This is Python 3
    str_input = input
    str_type = str


# some galleries reject requests if they're not coming from a browser- this is to get past that.
def urlopen_safe(url):
    q = Request(url)
    q.add_header('User-Agent', 'Mozilla/5.0')
    return urlopen(q)

def safe_makedirs(folder):
    if not os.path.exists(folder):
        os.makedirs(folder)


# Python 2<>3 compatibility methods
def encode_safe(in_str):
    try:
        if isinstance(in_str,unicode):
            in_str = in_str.encode("utf8")
    except:
        pass
    return in_str

def unicode_safe(str):
    try:
        str = str.decode("utf8")
    except:
        pass
    return str

def urlopen_text(url):
    return unicode_safe(urlopen_safe(url).read())
    
def is_str(obj):
    return isinstance(obj, str_type)

def is_iterable(obj):
    return hasattr(obj, '__iter__') and not is_str(obj)

