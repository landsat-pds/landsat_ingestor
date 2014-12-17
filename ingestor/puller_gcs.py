#!/usr/bin/env python

import argparse
import requests

def parse_scene(scene_root):
    """returns (sensor, path, row)"""

    # Root looks like 'LC80010082013237LGN00'

    assert scene_root[0] == 'L'
    assert len(scene_root) == 21

    return (scene_root[0:3], scene_root[3:6], scene_root[6:9])


def download_file(url, fn=None):
    if url.startswith('gs://'):
        url = re.sub(r'gs://(.*?)/', r'http://\1.storage.googleapis.com/', url)
    if not fn:
        fn = url.split('/')[-1]
    logging.info("downloading %s from %s", fn, url)
    r = plrequests.retry_get(url, stream=True)
    with open(fn, 'wb') as f:
        for d in r.iter_content(chunk_size=1024 * 1024 * 1024):
            if d:
                f.write(d)
    return fn


def build_url(scene_root):
    sensor, path, row = parse_scene(scene_root)

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
        for d in rv.iter_content(chunk_size=1024 * 1024 * 64):
            if d:
                f.write(d)

    # Confirm this is really a .bz file, not an http error or something.
    if open(filename).read(2) != 'BZ':
        raise Exception('%s does not appear to be a .bz file' % filename)

    return filename

