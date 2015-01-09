#!/usr/bin/env python

import argparse
import sys
import os
import shutil
import pprint

import puller
import splitter
import thumbnailer
import pusher
import scene_info
import index_maker

def process(source, scene_root, verbose=False, clean=False, list_file=None,
            overwrite=False):

    if pusher.check_existance(scene_root):
        print 'Scene %s already exists on destination bucket.' % scene_root
        if not overwrite:
            return None

    if verbose:
        print 'Processing scene: %s' % scene_root
        
    scene_dict = {}
    
    local_tarfile = puller.pull(source, scene_root, scene_dict,
                                verbose=verbose)

    local_dir = splitter.split(scene_root, local_tarfile, verbose=verbose)

    scene_info.add_mtl_info(scene_dict, scene_root, local_dir)
    
    thumbnailer.thumbnail(scene_root, local_dir, verbose=verbose)
    index_maker.make_index(scene_root, local_dir, verbose=verbose)
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
                         choices=['gcs', 'usgs'],
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

    if args.verbose:
        pprint.pprint(scene_dict)

if __name__ == '__main__':
    status = main(sys.argv[1:])
    sys.exit(status)
