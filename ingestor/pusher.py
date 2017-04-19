#!/usr/bin/env python

import sys
import os
import json
import socket
import datetime
import logging

from boto.s3.connection import S3Connection
from boto.s3.key import Key

import l8_aws_config
import l8_lib
from l8_lib import is_entity_id

s3_connection = None
s3_bucket = None

RUN_INFO_FILE = 'run_info.json'

BUCKET_URL = 'http://s3-us-west-2.amazonaws.com/landsat-pds'

def _get_bucket():
    global s3_connection
    global s3_bucket

    if s3_connection is None:
        if l8_aws_config.ACCESS_ID is None or l8_aws_config.ACCESS_KEY is None:
            logging.warning('S3 Access credentials missing, doing public access.')

        s3_connection = S3Connection(l8_aws_config.ACCESS_ID,
                                     l8_aws_config.ACCESS_KEY)

    if s3_bucket is None:
        s3_bucket = s3_connection.get_bucket(l8_aws_config.BUCKET_NAME)

    return s3_bucket

def _get_key(path, bucket=None):
    if bucket is None:
        bucket = _get_bucket()
    return bucket.get_key(path)

def push_file(src_path, s3_path, verbose=False, overwrite=False):
    key = _get_key(s3_path)
    if key is not None:
        if not overwrite:
            raise Exception('File already at %s' % s3_path)
        if verbose:
            print 'Overwriting existing %s.' % s3_path

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

def check_file_existance(s3_path):
    key = _get_key(s3_path)
    return key is not None

def get_file(s3_path, local_file=None):
    key = _get_key(s3_path)
    if key is None:
        raise Exception('%s not found' % s3_path)

    if local_file is None:
        local_file = os.path.basename(s3_path)

    key.get_contents_to_filename(local_file)
    return local_file

def unlink_file(s3_path):
    key = _get_key(s3_path)
    if key:
        key.delete()

def move_file(src_s3_path, dst_s3_path, overwrite=False):
    logging.debug('pusher.move_file(%s,%s)', src_s3_path, dst_s3_path)
    
    _get_bucket().copy_key(new_key_name = dst_s3_path,
                           src_bucket_name = l8_aws_config.BUCKET_NAME,
                           src_key_name = src_s3_path)
    unlink_file(src_s3_path)


def _scene_root_to_path(scene_root):
    sensor, path, row = l8_lib.parse_scene(scene_root)

    if is_entity_id(scene_root):
        path = 'L8/%s/%s/%s' % (path, row, scene_root)
    else:
        path = 'c1/L8/%s/%s/%s' % (path, row, scene_root)

    return path


def scene_url(scene_root):
    return l8_aws_config.BUCKET_URL + '/' + _scene_root_to_path(scene_root)

def check_existance(scene_root):
    dst_path = _scene_root_to_path(scene_root)
    thumb_path = '%s/%s_thumb_small.jpg' % (dst_path, scene_root)
    return _get_key(thumb_path) is not None
    
def push(scene_root, src_dir, scene_dict, verbose=False, overwrite=False):
    dst_path = _scene_root_to_path(scene_root)

    files = os.listdir(src_dir)
    idx = files.index('index.html')
    files.pop(idx)
    files.append('index.html')

    for filename in files:
        push_file(src_dir + '/' + filename,
                  dst_path + '/' + filename,
                  verbose=verbose, overwrite=overwrite)

    if scene_dict is not None:
        scene_dict['download_url'] = scene_url(scene_root) + '/index.html'

def pull_scene(scene_root, dst_dir=None, verbose=False, overwrite=False):
    src_path = _scene_root_to_path(scene_root)

    if dst_dir is None:
        dst_dir = scene_root

    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)
        
    for src_filename in list(src_path):
        dst_filename = os.path.join(dst_dir,os.path.basename(src_filename))
        if verbose:
            print 'Fetching %ss to %s' % (src_filename, dst_filename)
            
        key = _get_key(src_filename)
        key.get_contents_to_filename(dst_filename)

def acquire_run_id(comment='', force=False):
    
    key = _get_key(RUN_INFO_FILE)
    if key:
        run_info = json.loads(key.get_contents_as_string())
    else:
        key = Key(_get_bucket(), RUN_INFO_FILE)
        key.content_type = 'text/plain'
        run_info = {
            'last_run': 0, 
            'active_run': None,
            }

    if run_info['active_run'] is not None:
        print 'Already an active run:', run_info['active_run']
        if not force:
            raise Exception('Already an active run')

    run_info['active_run'] = '%s on %s started at %s %s' % (
        os.environ.get('USER','unknown'),
        socket.gethostname(),
        str(datetime.datetime.utcnow()),
        comment)
    
    key.set_contents_from_string(json.dumps(run_info))
        
    return run_info['last_run'] + 1

def upload_run_list(run_id, run_filename, scene_list_filename, verbose=False):
    run_info_key = _get_key(RUN_INFO_FILE)
    run_info = json.loads(run_info_key.get_contents_as_string())

    if run_info['last_run'] != run_id-1 or run_info['active_run'] is None:
        raise Exception('We are not the active run! ' + str(run_info))
        
    if socket.gethostname() not in run_info['active_run']:
        raise Exception('We are not the active run host! ' + str(run_info))

    if verbose:
        print 'Confirmed we are the active run: ', str(run_info)

    run_info['last_run'] = run_id
    run_info['active_run'] = None

    run_s3_name = 'runs/%s.csv' % run_id

    run_key = Key(_get_bucket(), run_s3_name)
    run_key.set_contents_from_filename(run_filename)

    if verbose:
        print 'Uploaded run log %s to %s on s3.' % (run_filename, run_s3_name)

    os.system('gzip -f -9 %s' % scene_list_filename)
    key = _get_key('scene_list.gz')
    key.set_contents_from_filename(scene_list_filename + '.gz')
    
    if verbose:
        print 'Uploaded %s to scene_list.gz' % scene_list_filename

    run_info_key.set_contents_from_string(json.dumps(run_info))

    if verbose:
        print 'last run incremented, active_run over.'
        
def get_past_list():
    key = _get_key('scene_list.gz')
    if not key:
        open('scene_list','w').write('\n')
    else:
        key.get_contents_to_filename('scene_list.gz')
        os.system('gzip -f -d scene_list.gz')

    return 'scene_list'


def get_past_collection_list():
    key = _get_key('c1/L8/scene_list.gz')
    key.get_contents_to_filename('scene_list.gz')
    os.system('gzip -f -d scene_list.gz')

    return 'scene_list'


def list(prefix='', limit=None):
    bucket = _get_bucket()
    for x in bucket.list(prefix=prefix):
        yield x.name
    
if __name__ == '__main__':
    if len(sys.argv) != 3:
        print 'Usage: pusher.py <scene_root> <scene_dir_path>'
        sys.exit(1)
        
    scene_dict = {}
    push(sys.argv[1], sys.argv[2], scene_dict)
