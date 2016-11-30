import re
try:
    import urllib.request as urllib
except:
    import urllib # Python 2

def title(source):
    gfyId = re.findall(r'href=\".*gfycat.com/(\w+).*\">', source)[-1]
    link = 'https://gfycat.com/cajax/get/' + gfyId
    respond = urllib.urlopen(link).read()
    username = re.findall(r'\"userName\":\"(.+?)\",' ,respond)[0]
    if username == "anonymous":
        username = "gfycat" + gfyId
    return username

def redirect(source):
    gfyId = re.findall(r'href=\".*gfycat.com/(\w+).*\">', source)[-1]
    respond = urllib.urlopen('https://gfycat.com/cajax/get/' + gfyId).read()
    webmurl = re.findall(r'\"webmUrl\":\"(.+?)\",' ,respond)[0]
    # delete escape characters
    webmurl = webmurl.replace("\\","")
    # for some reason we can not connect via https
    webmurl = webmurl.replace("https", "http")
    return webmurl
same_filename = True
