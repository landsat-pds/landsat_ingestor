#!/usr/bin/env python

import sys
import os
import argparse
import requests

from usgs import api

import l8_lib

def get_download_url(scene_root):
    urls = api.download('LANDSAT_8', 'EE', [scene_root], 'STANDARD')
    print urls
    return urls[0]

def pull(scene_root, scene_dict, verbose=False):
    filename = scene_root + '.tar.gz'

    url = get_download_url(scene_root)
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
    if open(filename).read(2) != '\037\0213':
        raise Exception('%s does not appear to be a .bz file' % filename)

    if verbose:
        print '%s successfully downloaded (%d bytes)' % (
            filename, os.path.getsize(filename))

    if scene_dict is not None:
        scene_dict['src_url'] = url
        scene_dict['src_md5sum'] = l8_lib.get_file_md5sum(filename)
        
    return filename

