import os, time

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
    q.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36')
    return urlopen(q)

JS_DRIVER = None
def urlopen_js(url):
    global JS_DRIVER
    if not JS_DRIVER:
        try:
            from selenium import webdriver
            from chromedriver_py import binary_path
        except:
            raise Exception("Page requires JavaScript, please run 'pip install selenium chromedriver-py' and try again")
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        JS_DRIVER = webdriver.Chrome(executable_path=binary_path, options=options)
    JS_DRIVER.get(url)
    wall_button = JS_DRIVER.find_elements_by_xpath("//div[@class='Wall-Button Button btn-wall--yes']")
    if wall_button:
        wall_button[0].click()
    more_button = JS_DRIVER.find_elements_by_xpath("//button[@class='loadMore']")
    if more_button:
        more_button[0].click()
    return JS_DRIVER.page_source

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
        return str.decode("utf8")
    except:
        pass
    try:
        return str.decode("latin1")
    except:
        return str

def urlopen_text(url, wait_time = 0):
    data = urlopen_safe(url)
    # some galleries need time to finish loading a page
    time.sleep(wait_time)
    return unicode_safe(data.read())
    
def is_str(obj):
    # isinstance doesn't always work here
    return obj.__class__.__name__ == str_type.__name__

def is_iterable(obj):
    return hasattr(obj, '__iter__') and not is_str(obj)

