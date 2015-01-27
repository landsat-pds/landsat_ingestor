#!/usr/bin/env python

import sys
import os
import argparse
import requests

import l8_lib
import pusher

def clean_queued_tarfile(scene_root, verbose=False):
    if verbose:
        print 'pusher.unlink_file(%s)' % s3_path(scene_root)
    pusher.unlink_file(s3_path(scene_root))

def s3_path(scene_root):
    return 'tarq/%s.tar.gz' % scene_root

def build_url(scene_root):
    return 'https://s3-us-west-2.amazonaws.com/landsat-pds/%s' % (
        s3_path(scene_root))

def pull(scene_root, scene_dict, verbose=False):
    filename = scene_root + '.tar.gz'

    url = build_url(scene_root)
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

    # Confirm this is really a .gz or .bz file, not an http error or something.
    header = open(filename).read(2)
    if header != '\037\213' and header != 'BZ':
        raise Exception('%s does not appear to be a .gz or .bz file' % filename)

    if verbose:
        print '%s successfully downloaded (%d bytes)' % (
            filename, os.path.getsize(filename))

    return filename
