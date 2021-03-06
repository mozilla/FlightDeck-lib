#!/usr/bin/env python
# Really simple rudimentary benchmark to compare ConnectionPool versus standard
# urllib to demonstrate the usefulness of connection re-using.

# URLs to download. Doesn't matter as long as they're from the same host, so we
# can take advantage of connection re-using.
TO_DOWNLOAD = [
    'http://code.google.com/apis/apps/',
    'http://code.google.com/apis/base/',
    'http://code.google.com/apis/blogger/',
    'http://code.google.com/apis/calendar/',
    'http://code.google.com/apis/codesearch/',
    'http://code.google.com/apis/contact/',
    'http://code.google.com/apis/books/',
    'http://code.google.com/apis/documents/',
    'http://code.google.com/apis/finance/',
    'http://code.google.com/apis/health/',
    'http://code.google.com/apis/notebook/',
    'http://code.google.com/apis/picasaweb/',
    'http://code.google.com/apis/spreadsheets/',
    'http://code.google.com/apis/webmastertools/',
    'http://code.google.com/apis/youtube/',
]

import sys
sys.path.append('../')

from urllib3 import HTTPConnectionPool
import urllib
import time

def urllib_get(url_list):
    assert url_list
    for url in url_list:
        now = time.time()
        r = urllib.urlopen(url)
        elapsed = time.time() - now
        print "Got in %0.3f: %s" % (elapsed, url)

def pool_get(url_list):
    assert url_list
    pool = HTTPConnectionPool.from_url(url_list[0])
    for url in url_list:
        now = time.time()
        r = pool.get_url(url)
        elapsed = time.time() - now
        print "Got in %0.3fs: %s" % (elapsed, url)

if __name__ == '__main__':
    print "Running pool_get ..."
    now = time.time()
    pool_get(TO_DOWNLOAD)
    pool_elapsed = time.time() - now

    print "Running urllib_get ..."
    now = time.time()
    urllib_get(TO_DOWNLOAD)
    urllib_elapsed = time.time() - now

    print "Completed pool_get in %0.3fs" % pool_elapsed
    print "Completed urllib_get in %0.3fs" % urllib_elapsed


"""
Example results:

Completed pool_get in 1.163s
Completed urllib_get in 2.318s
"""
