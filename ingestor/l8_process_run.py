#!/usr/bin/env python

import argparse
import sys
import os
import shutil
import pprint
import sets

from usgs import api

import pusher
import scene_info
import l8_process_scene

def query_for_scenes(start_date, end_date, limit=None):
    full_list = []
    list_offset = 0
    these_scenes = 'start'
    chunk_size = 500
    if limit is not None and limit < chunk_size:
        chunk_size = limit
    
    print 'search...'
    while these_scenes == 'start' or len(these_scenes) == chunk_size:
        these_scenes = api.search("LANDSAT_8", "EE",
                                  start_date=start_date, end_date=end_date,
                                  starting_number = 1+list_offset,
                                  max_results=chunk_size)
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
    
    cmd = 'parallel -j 6 %s %s -l %s < %s' % (
        'l8_process_scene.py',
        '--verbose' if args.verbose else '',
        run_file,
        in_file)
    if args.verbose:
        print cmd
    rc = os.system(cmd)
    
    new_lines = open(run_file).read().split('\n')[1:]
    open(scene_list_file,'a').write(('\n'.join(new_lines)) + '\n')

    pusher.upload_run_list(run_id, run_file, scene_list_file,
                           verbose = args.verbose)

def get_parser():
    aparser = argparse.ArgumentParser(
        description='Query for new scenes and ingest them to S3.')

    aparser.add_argument('-s', '--source', default='gcs',
                         choices=['gcs', 'usgs'],
                         help='Source service for tar')
    aparser.add_argument('-v', '--verbose', action='store_true',
                         help='Report details on progress.')
    aparser.add_argument('--limit', type=int)
    aparser.add_argument('--start-date')
    aparser.add_argument('--end-date')
    aparser.add_argument('--run-directly', action='store_true')
    aparser.add_argument('--parallel', action='store_true')
    aparser.add_argument('--break-run-lock', action='store_true')
    return aparser

def main(rawargs):
    args = get_parser().parse_args(rawargs)
    scene_ids = query_for_scenes(args.start_date, args.end_date,
                                 limit=args.limit)
    scene_list_file = pusher.get_past_list()
    scene_ids = remove_processed_ids(scene_ids, scene_list_file)

    if not args.run_directly:
        for i in scene_ids:
            print i
        sys.exit(1)

    elif args.parallel:
        process_scene_set_external(args, scene_ids, scene_list_file)
    else:
        process_scene_set_internal(args, scene_ids, scene_list_file)

if __name__ == '__main__':
    status = main(sys.argv[1:])
    sys.exit(status)
