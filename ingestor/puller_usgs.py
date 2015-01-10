#!/usr/bin/env python

import sys
import os
import argparse
import requests

from usgs import api

import l8_lib

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

    rv = requests.get(url, stream=True)
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

    if scene_dict is not None:
        scene_dict['src_url'] = url
        scene_dict['src_md5sum'] = l8_lib.get_file_md5sum(filename)
        
    return filename

