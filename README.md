# gallery_get & reddit_get

**Python suite for batch-downloading images from galleries.**

## Introduction

Many galleries make it hard to download all the images from a gallery.  Their image links often redirect to a viewing page rather than the image itself, making it hard to grab all the images on a page (even with popular browser plugins).  To get around this, gallery_get opens the redirect-links and grabs images from there.

It comes with a few "plugins" customized for certain sites, along with a generic fallback plugin that works on multiple galleries.  Note that galleries will change their markup from time to time, so these plugins may need to be updated to catch up with such changes.

reddit_get is a Python tool for batch-downloading all imgur albums and pictures submitted by any reddit user.  It relies on gallery_get.
	

## Requirements

1. Python - Has been tested on the following versions:
 - 2.7.2 on OSX
 - 2.7.3 on Windows Vista

2. Clone or download this repository.  It won't run without the gallery_plugins subfolder.


## Usage

### Without Parameters
 
```
$ python gallery_get.py
```

```
$ python reddit_get.py
```

You will be prompted for the gallery URL (for gallery_get) or reddit user (for reddit_get).  You will also be prompted for a destination directory, which it will remember as default for next time.


### With Parameters

```
$ python gallery_get.py [URL-OF-GALLERY] [DEST]
```

```
$ python reddit_get.py [REDDIT-USERNAME] [DEST]
```

If don't specify a destination directory, it will look for the contents of last_gallery_dest.txt, falling back on the current working directory.


## Contribute

Feel free to add your own plugins or make updates if you're familiar with regular expressions and/or Python logic!

Each plugin overrides the following with a string, regular expression, or function.

- title
- redirect links
- image links
- whether to use the same filename from the site, or use "001", "002", etc.

See comments on existing plugins for more usage info.


## License

Licensed under the MIT License.
