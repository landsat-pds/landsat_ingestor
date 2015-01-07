#!/usr/bin/env python

import sys
import argparse
import requests

import l8_lib

def build_url(scene_root):
    sensor, path, row = l8_lib.parse_scene(scene_root)

    assert sensor == 'LC8'

    return '%s/landsat/L8/%s/%s/%s.tar.bz' % (
        'http://earthengine-public.storage.googleapis.com',
        path,
        row,
        scene_root)

def pull(scene_root):
    filename = scene_root + '.tar.bz'

    url = build_url(scene_root)

    rv = requests.get(url, stream=True)
    rv.raise_for_status()

    with open(filename, 'wb') as f:
        for d in rv.iter_content(chunk_size=1024 * 1024 * 10):
            if d:
                f.write(d)
                sys.stderr.write('.')
                sys.stderr.flush()

    sys.stderr.write('\n')

    # Confirm this is really a .bz file, not an http error or something.
    if open(filename).read(2) != 'BZ':
        raise Exception('%s does not appear to be a .bz file' % filename)

    return filename

