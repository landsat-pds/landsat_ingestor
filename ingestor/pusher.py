#!/usr/bin/env python

import sys
import os

from boto.s3.connection import S3Connection
from boto.s3.key import Key

import l8_aws_config
import l8_lib

s3_connection = None
s3_bucket = None

def _get_bucket():
    global s3_connection
    global s3_bucket

    if s3_connection is None:
        s3_connection = S3Connection(l8_aws_config.ACCESS_ID,
                                     l8_aws_config.ACCESS_KEY)

    if s3_bucket is None:
        s3_bucket = s3_connection.get_bucket(l8_aws_config.BUCKET_NAME)

    return s3_bucket

def _get_key(path, bucket=None):
    if bucket is None:
        bucket = _get_bucket()
    return bucket.get_key(path)

def _push_file(src_path, s3_path, verbose=False):
    key = _get_key(s3_path)
    if key is not None:
        raise Exception('File already at %s' % s3_path)

    key = Key(_get_bucket(), s3_path)
    if s3_path.endswith('.TIF') or s3_path.endswith('.tif'):
        key.content_type = 'image/tiff'
    if s3_path.endswith('.jpg'):
        key.content_type = 'image/jpeg'
    if s3_path.endswith('.txt'):
        key.content_type = 'text/plain'

    bytes_uploaded = key.set_contents_from_filename(src_path)
    if verbose:
        print 'Uploaded %d bytes from %s to %s.' % (
            bytes_uploaded, src_path, s3_path)

def _scene_root_to_path(scene_root):
    sensor, path, row = l8_lib.parse_scene(scene_root)

    return 'L8/%s/%s/%s' % (path, row, scene_root)

def check_existance(scene_root):
    dst_path = _scene_root_to_path(scene_root)
    thumb_path = '%s/%s_thumb_small.jpg' % (dst_path, scene_root)
    return _get_key(thumb_path) is not None
    
def push(scene_root, src_dir, verbose=False):
    dst_path = _scene_root_to_path(scene_root)

    for filename in os.listdir(src_dir):
        _push_file(src_dir + '/' + filename,
                   dst_path + '/' + filename,
                   verbose=verbose)

def acquire_run_id():
    return 1

def upload_run_list(run_id, scene_list):
    pass

def get_past_list():
    return ''

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print 'Usage: pusher.py <scene_root> <scene_dir_path>'
        sys.exit(1)
        
    push(sys.argv[1], sys.argv[2])
