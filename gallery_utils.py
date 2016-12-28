# Python 3 imports that throw in Python 2
try:
    from urllib.request import Request, urlopen
except ImportError:
    # This is Python 2
    from urllib2 import Request, urlopen

# Python 2 types that throw in Python 3
try:
    str_input = raw_input
    str_type = basestring
except:
    # This is Python 3
    str_input = input
    str_type = str

# Python 2<>3 compatibility methods
def unicode_safe(str):
    try:
        str = str.decode("utf8")
    except:
        pass
    return str

def encode_safe(in_str):
    try:
        if isinstance(in_str,unicode):
            in_str = in_str.encode("utf8")
    except:
        pass
    return in_str

import time
# some galleries reject requests if they're not coming from a browser- this is to get past that.
def urlopen_safe(url):
    q = Request(url)
    q.add_header('User-Agent', 'Mozilla/5.0')
    return urlopen(q)