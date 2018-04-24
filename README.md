# gallery_get & reddit_get

**Python suite for batch-downloading images from galleries.**

## Introduction

Many galleries make it hard to download all the images from a gallery.  Their image links often redirect to a viewing page rather than the image itself, making it hard to grab all the images on a page (even with popular browser plugins).  To get around this, gallery_get opens the redirect-links and grabs images from there.

reddit_get grabs all imgur albums and pictures submitted by a given reddit user.  It relies on gallery_get.


## Tested Versions and Galleries

Platforms, Python Versions:

* OSX (Python 2.7.2 and 3.5.1)
* Windows (Python 2.7.3 and 3.6.0)

Gallery Plugins:

* 4chan
* eroshare
* fuskator
* gfycat
* gogoimage
* imagefap
* imagevenue
* imgbox
* imgur (albums and galleries)
* Pornhub (albums and single videos)
* shimmie
* vidble
* xHamster
* xVideos

Generic Plugin works for:

* alafoto.com
* forum.phun.org
* setsdb.org
* (more)

## Installation

You can download this repository from GitHub, or grab it from PyPI:

```
$ pip install gallery_get
```

PyPI page is here: https://pypi.python.org/pypi/gallery_get

## Usage

### From the Command Line
 
```
$ python gallery_get.py
$ python gallery_get.py [URL-OF-GALLERY]
$ python gallery_get.py [URL-OF-GALLERY] [DEST]
```

```
$ python reddit_get.py
$ python reddit_get.py [REDDIT-USERNAME]
$ python reddit_get.py [REDDIT-USERNAME] [DEST]
```

If you call with no parameters, you'll be prompted for the gallery URL (for gallery_get) or reddit user (for reddit_get).  You will also be prompted for a destination directory, which it will remember as the default for next time.

If you skip [DEST] it will look for the contents of last_gallery_dest.txt, falling back on the current working directory.

### From the Python Environment

```
import gallery_get
gallery_get.run()
gallery_get.run(URL)
gallery_get.run(URL, DESTINATION)
```

```
import reddit_get
reddit_get.run()
reddit_get.run(USER)
reddit_get.run(USER, DESTINATION)
```
Skipping parameters results in same corresponding behavior indicated above.

## Notes

If you run gallery_get or reddit_get on the same URL/user and destination more than once, it will skip the already-existing images next time (unless the size has changed).  This allows you to do incremental updates.

gallery_get comes with a few "plugins" customized for certain sites, along with a generic fallback plugin that works on multiple galleries.  Note that galleries will change their markup from time to time, so these plugins may need to be updated to catch up with such changes.  (Which brings us to the next section...)

## Testing

I've provided a testing suite called gallery_get_test.py that will run gallery_get/reddit_get with provided URLs and users.  Options are as follows
```
  --noprompt          don't prompt for extra galleries
  --input=INPUT_PATH  input CSV for testing (same format as output)
```
INPUT_PATH defaults to gallery_get_test_input.csv (provided)
The output is gallery_get_test_output.csv

To add a new gallery/user to the test:

  1. run gallery_get_test.py
  2. enter your gallery/user
  3. repeat step 2 for additional galleries/users
  4. if the output looks ok, replace gallery_get_test_input.csv with gallery_get_test_output.csv

## Contribute

Feel free to add your own plugins or make updates if you're familiar with regular expressions and/or Python logic!

Each plugin overrides the following with a string, regular expression, or function.

- title
- redirect links
- image links
- whether to use the same filename from the site, or use "001", "002", etc.

See comments in the existing plugin files for more details.


## License

Licensed under the MIT License.
