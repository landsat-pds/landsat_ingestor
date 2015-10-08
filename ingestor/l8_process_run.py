#!/usr/bin/env python

import argparse
import sys
import os
import shutil
import pprint
import sets
import time

from usgs import api
from usgs import USGSError

import pusher
import scene_info
import l8_process_scene
from puller_usgs import backoff_factor


def retry_login(retries=4, verbose=False):
    """
    Retry USGS login multiple times, with exponential backoff between
    """
    if verbose:
        print 'logging in...'
    
    sleep_time = 5

    for _ in xrange(retries + 1):
        
        try:
            api_key = api.login(os.environ['USGS_USERID'], os.environ['USGS_PASSWORD'])
            if verbose:
                print '  api_key = %s' % api_key
            return api_key
        
        except USGSError:
            pass
        
        print 'USGS login failed, retry in %s' % sleep_time
            
        time.sleep(sleep_time)
        sleep_time *= backoff_factor(2)
    
    return None


def query_for_scenes(start_date, end_date, verbose=False, limit=None):
    
    if 'USGS_PASSWORD' in os.environ:
        api_key = retry_login(verbose=verbose)
    
    if not api_key:
        print "Failed to authenticate with USGS servers"
        sys.exit(1)

    full_list = []
    list_offset = 0
    these_scenes = 'start'
    chunk_size = 500
    if limit is not None and limit < chunk_size:
        chunk_size = limit

    if verbose:
        print 'search...'
    while these_scenes == 'start' or len(these_scenes) == chunk_size:
        these_scenes = api.search("LANDSAT_8", "EE",
                                  start_date=start_date, end_date=end_date,
                                  starting_number = 1+list_offset,
                                  max_results=chunk_size)
        if verbose:
            print '... %d scenes' % len(these_scenes)
        full_list += these_scenes
        list_offset += len(these_scenes)

        if limit is not None and list_offset >= limit:
            break
        
    scene_ids = [scene['entityId'] for scene in full_list]
    return scene_ids

def remove_processed_ids(scene_ids, scene_list_file):
    prev_scene_ids = sets.Set([
     line[:line.find(',')] for line in open(
                scene_list_file).readlines()])

    missing_ids = []
    for scene_id in scene_ids:
        if scene_id not in prev_scene_ids:
            missing_ids.append(scene_id)

    return missing_ids

def remove_queued_ids(scene_ids):
    missing_ids = []
    for scene_id in scene_ids:
        if not pusher.check_file_existance('tarq/%s.tar.gz' % scene_id):
            missing_ids.append(scene_id)
    return missing_ids
            
def process_scene_set_internal(args, scene_ids, scene_list_file):
    run_id = pusher.acquire_run_id('(l8_process_run.py)',
                                   force=args.break_run_lock)

    run_file = 'this_run.csv'
    scene_info.init_list_file(run_file)

    results = []
    for scene_id in scene_ids:

        scene_dict = l8_process_scene.process(
            args.source, scene_id,
            clean = True,
            verbose = args.verbose)

        if scene_dict is not None:
            open(run_file,'a').write(
                scene_info.make_scene_line(scene_dict)+'\n')
            open(scene_list_file,'a').write(
                scene_info.make_scene_line(scene_dict)+'\n')

    pusher.upload_run_list(run_id, run_file, scene_list_file,
                           verbose = args.verbose)

def process_scene_set_external(args, scene_ids, scene_list_file):
    run_id = pusher.acquire_run_id('(l8_process_run.py)',
                                   force=args.break_run_lock)

    run_file = 'this_run.csv'
    scene_info.init_list_file(run_file)

    in_file = 'this_run.lst'
    open(in_file,'w').write(('\n'.join(scene_ids)) + '\n')
    
    cmd = 'parallel --gnu -j 6 %s %s -l %s < %s' % (
        'l8_process_scene.py',
        '--verbose' if args.verbose else '',
        run_file,
        in_file)
    if args.verbose:
        print cmd
    rc = os.system(cmd)
    
    new_lines = open(run_file).read().strip().split('\n')[1:]
    open(scene_list_file,'a').write(('\n'.join(new_lines)) + '\n')

    pusher.upload_run_list(run_id, run_file, scene_list_file,
                           verbose = args.verbose)

def copy_scene_set_external(args, scene_ids):
    in_file = 'this_run.lst'
    open(in_file,'w').write(('\n'.join(scene_ids)) + '\n')
    
    cmd = 'parallel --gnu --delay 10 -j 2 %s %s --source %s < %s' % (
        'l8_queue_tar.py',
        '--verbose' if args.verbose else '',
        args.source,
        in_file)
    if args.verbose:
        print cmd
    rc = os.system(cmd)
    if args.verbose:
        print 'status=%d, %d scenes requested.' % (rc, len(scene_ids))
    
def get_parser():
    aparser = argparse.ArgumentParser(
        description='Query for new scenes and ingest them to S3.')

    aparser.add_argument('-s', '--source', default='usgs',
                         choices=['gcs', 'usgs', 'auto'],
                         help='Source service for tar')
    aparser.add_argument('-v', '--verbose', action='store_true',
                         help='Report details on progress.')
    aparser.add_argument('--limit', type=int)
    aparser.add_argument('--start-date')
    aparser.add_argument('--end-date')
    aparser.add_argument('--run-directly', action='store_true')
    aparser.add_argument('--queue', action='store_true')
    aparser.add_argument('--parallel', action='store_true')
    aparser.add_argument('--break-run-lock', action='store_true')
    return aparser

def main(rawargs):
    args = get_parser().parse_args(rawargs)
    scene_ids = query_for_scenes(args.start_date, args.end_date,
                                 verbose=args.verbose,
                                 limit=args.limit)
    scene_list_file = pusher.get_past_list()
    scene_ids = remove_processed_ids(scene_ids, scene_list_file)

    if args.queue:
        scene_ids = remove_queued_ids(scene_ids)

    print '%d scenes identified for processing.' % len(scene_ids)
    sys.stdout.flush()

    if not args.run_directly and not args.queue:
        for i in scene_ids:
            print i
        sys.exit(1)

    if args.queue:
        copy_scene_set_external(args, scene_ids)
    elif args.parallel:
        process_scene_set_external(args, scene_ids, scene_list_file)
    else:
        process_scene_set_internal(args, scene_ids, scene_list_file)
    
    api.logout()


if __name__ == '__main__':
    status = main(sys.argv[1:])
    sys.exit(status)
