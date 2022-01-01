# to test locally:
# python setup.py develop
#
# to deploy:
# rm -rf ./dist
# python setup.py sdist bdist_wheel
# python -m twine upload --repository pypi dist/*
#
# more info here:
# https://packaging.python.org/tutorials/packaging-projects/#uploading-your-project-to-pypi

# NOTE: make sure you have the latest setuptools or the requirements may not get installed correctly.
# python -m pip install --upgrade pip setuptools

import setuptools

setuptools.setup(name = 'gallery_get',
    version = '1.9.2',
    author = 'Rego Sen',
    author_email = 'regosen@gmail.com',
    url = 'https://github.com/regosen/gallery_get',
    description = 'Gallery downloader - supports many galleries and reddit user histories',
    long_description = open('README.rst', 'r').read(),
    long_description_content_type = 'text/markdown',
    license = 'MIT',
    keywords = 'gallery downloader reddit imgur imgbox 4chan xhamster eroshare vidble pornhub xvideos imagebam alphacoders',
    packages = setuptools.find_packages(),
    include_package_data = True,
    install_requires = [
        'chromedriver-py',
        'selenium',
    ],
    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Internet',
        'Topic :: Multimedia :: Graphics',
    ],
    entry_points = {
        'console_scripts': [
            'gallery_get = gallery_get:main',
            'reddit_get = reddit_get:main',
        ]
    },
)