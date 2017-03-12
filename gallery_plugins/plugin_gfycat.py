import re
from gallery_utils import *

def title(source):
    gfyId = re.findall(r'href=\".*gfycat.com/(\w+).*\">', source)[-1]
    link = 'https://gfycat.com/cajax/get/' + gfyId
    respond = urlopen_text(link)
    username = re.findall(r'\"userName\":\"(.+?)\",' ,respond)[0]
    return username if username != "anonymous" else "gfycat " + gfyId

def redirect(source):
    gfyId = re.findall(r'href=\".*gfycat.com/(\w+).*\">', source)[-1]
    respond = urlopen_text('https://gfycat.com/cajax/get/' + gfyId)
    webmurl = re.findall(r'\"webmUrl\":\"(.+?)\",' ,respond)[0]
    # delete escape characters
    webmurl = webmurl.replace("\\","")
    # for some reason we can not connect via https
    webmurl = webmurl.replace("https", "http")
    return webmurl
same_filename = True
