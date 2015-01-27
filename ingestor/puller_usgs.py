#!/usr/bin/env python

import sys
import os
import argparse
import requests
import time
import random

from usgs import api

import l8_lib

def backoff_factor(base):
    """Add a small amount of random jitter to avoid cyclic server stampedes"""

    return base + round(random.random() % 0.5, 2)

def is_success(rv):
    if rv.status_code >= 400:
        return False
    return True

def is_retryable(rv):
    return rv.status_code >= 503

def retry_get(url, retries=4, **kwargs):
    """retry get multiple times, with exponential backoff between"""

    sleep_time = 5

    for _ in xrange(retries + 1):
        rv = requests.get(url, **kwargs)
        if rv is None or rv.status_code != 503:
            return rv

        print 'GET %s reports code %s, retry in %s' % (
            url, rv.status_code, sleep_time)

        time.sleep(sleep_time)
        sleep_time *= backoff_factor(2)

    return rv

def get_download_url(scene_root, verbose):
    if 'USGS_PASSWORD' in os.environ:
        if verbose:
            print 'logging in...'
        api_key = api.login(os.environ['USGS_USERID'],
                            os.environ['USGS_PASSWORD'])
        if verbose:
            print '  api_key = %s' % api_key


    urls = api.download('LANDSAT_8', 'EE', [scene_root], 'STANDARD')
    return urls[0]

def pull(scene_root, scene_dict, verbose=False):
    filename = scene_root + '.tar.gz'

    url = get_download_url(scene_root, verbose=verbose)
    if verbose:
        print 'Fetching:', url

    rv = retry_get(url, stream=True)
    rv.raise_for_status()

    with open(filename, 'wb') as f:
        for d in rv.iter_content(chunk_size=1024 * 1024 * 10):
            if d:
                f.write(d)
                if verbose:
                    sys.stdout.write('.')
                    sys.stdout.flush()

    if verbose:
        sys.stdout.write('\n')

    # Confirm this is really a .gz file, not an http error or something.
    if open(filename).read(2) != '\037\213':
        raise Exception('%s does not appear to be a .gz file' % filename)

    if verbose:
        print '%s successfully downloaded (%d bytes)' % (
            filename, os.path.getsize(filename))

    return filename

