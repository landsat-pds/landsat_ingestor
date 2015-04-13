#!/usr/bin/env python

import argparse
import sys
import os
import shutil
import pprint
import requests

import puller
import puller_s3queue
import splitter
import thumbnailer
import pusher
import scene_info
import scene_index_maker

def collect_missing_entry(scene_root, verbose, clean, list_file):
    scene_dict = {}

    mtl_file = scene_root + '_MTL.txt'
    mtl_url = pusher.scene_url(scene_root) + '/' + mtl_file

    rv = requests.get(mtl_url)
    rv.raise_for_status()

    with open(mtl_file, 'wb') as f:
        for chunk in rv.iter_content(chunk_size=1000000):
            f.write(chunk)
            
    scene_info.add_mtl_info(scene_dict, scene_root, '.')
    scene_dict['download_url'] = pusher.scene_url(scene_root) + '/index.html'
    
    if list_file:
        scene_info.append_scene_line(list_file, scene_dict)

    if clean:
        os.unlink(mtl_file)
        
    return scene_dict

def process(source, scene_root, verbose=False, clean=False, list_file=None,
            overwrite=False):

    if pusher.check_existance(scene_root):
        print 'Scene %s already exists on destination bucket.' % scene_root
        if not overwrite:
            return collect_missing_entry(scene_root, verbose, clean, list_file)

    if verbose:
        print 'Processing scene: %s' % scene_root
        
    scene_dict = {}
    
    local_tarfile = puller.pull(source, scene_root, scene_dict,
                                verbose=verbose)

    try:
        local_dir = splitter.split(scene_root, local_tarfile, verbose=verbose)
    except:
        if source is 's3queue':
            puller_s3queue.move_to_corrupt_queue(scene_root)
            return

    scene_info.add_mtl_info(scene_dict, scene_root, local_dir)
    
    thumbnailer.thumbnail(scene_root, local_dir, verbose=verbose)
    scene_index_maker.make_index(scene_root, local_dir, verbose=verbose)
    pusher.push(scene_root, local_dir, scene_dict, verbose=verbose, overwrite=overwrite)

    if clean:
        os.unlink(local_tarfile)
        shutil.rmtree(local_dir)

    if list_file:
        scene_info.append_scene_line(list_file, scene_dict)

    return scene_dict
    

def get_parser():
    aparser = argparse.ArgumentParser(
        description='Process one Landsat scene from source to S3.')

    aparser.add_argument('-s', '--source', default='usgs',
                         choices=['gcs', 'usgs', 's3queue', 'auto'],
                         help='Source service for tar')
    aparser.add_argument('-o', '--overwrite', action='store_true',
                         help='overwite an existing scene if it exists')
    aparser.add_argument('-c', '--clean', action='store_true',
                         help='clean up all intermediate files')
    aparser.add_argument('-v', '--verbose', action='store_true',
                         help='Report details on progress.')
    aparser.add_argument('-l', '--list-file', 
                         help='List .csv file to append processing record to.')
    aparser.add_argument('scene',
                         help='Scene name, ie. LC82301202013305LGN00')
    return aparser

def main(rawargs):
    args = get_parser().parse_args(rawargs)
    scene_dict = process(args.source, args.scene,
                         verbose = args.verbose,
                         clean = args.clean,
                         list_file = args.list_file,
                         overwrite = args.overwrite)

    if args.source == 's3queue':
        puller_s3queue.clean_queued_tarfile(args.scene, verbose=args.verbose)

    if args.verbose:
        pprint.pprint(scene_dict)

if __name__ == '__main__':
    status = main(sys.argv[1:])
    sys.exit(status)
