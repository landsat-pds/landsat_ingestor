#!/usr/bin/env python

import sys
import os
import argparse
import requests
import boto
import datetime

import l8_lib
import pusher

def clean_queued_tarfile(scene_root, verbose=False):
    if verbose:
        print 'pusher.unlink_file(%s)' % s3_path(scene_root)
    pusher.unlink_file(s3_path(scene_root))

def s3_path(scene_root):
    return 'tarq/%s.tar.gz' % scene_root

def build_url(scene_root):
    return '%s/%s' % (pusher.BUCKET_URL, s3_path(scene_root))


def move_to_corrupt_queue(scene_root):
    """
    :param scene_root:
        Landsat scene id
    """
    
    src_s3_path = s3_path(scene_root)
    dst_s3_path = 'tarq_corrupt/%s.tar.gz' % scene_root
    pusher.move_file(src_s3_path, dst_s3_path, overwrite=True)
    print 'Migrating corrupt input to %s/%s' % (
        pusher.BUCKET_URL,
        dst_s3_path)

def pull(scene_root, scene_dict, verbose=False):
    filename = scene_root + '.tar.gz'

    url = build_url(scene_root)
    if verbose:
        print 'Fetching:', url

    rv = requests.get(url, stream=True, timeout=120)
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
        src_s3_path = s3_path(scene_root)
        last_modified = boto.utils.parse_ts(
            pusher._get_key(src_s3_path).last_modified)

        oldness = datetime.datetime.now() - last_modified
        if oldness.seconds > 3600:
            move_to_corrupt_queue(scene_root)
        else:
            print 'Leave %s in tarq, it may still be uploading.'
        
        raise Exception('%s does not appear to be a .gz or .bz file'%filename)

    if verbose:
        print '%s successfully downloaded (%d bytes)' % (
            filename, os.path.getsize(filename))

    return filename
