#!/usr/bin/env python

import argparse
import sys
import os
import shutil

import puller
import splitter
import thumbnailer
import pusher
import scene_info

def process(source, scene_root, verbose=False, clean=False):
    if pusher.check_existance(scene_root):
        print 'Scene %s already exists on destination bucket.' % scene_root

    if verbose:
        print 'Processing scene: %s' % scene_root
        
    scene_dict = {}
    
    local_tarfile = puller.pull(source, scene_root, verbose=verbose)

    local_dir = splitter.split(scene_root, local_tarfile, verbose=verbose)

    scene_info.add_mtl_info(scene_dict, scene_root, local_dir)
    
    thumbnailer.thumbnail(scene_root, local_dir, verbose=verbose)
    pusher.push(scene_root, local_dir, verbose=verbose)

    if clean:
        os.unlink(local_tarfile)
        shutil.rmtree(local_dir)
    

def get_parser():
    aparser = argparse.ArgumentParser(
        description='Process one Landsat scene from source to S3.')

    aparser.add_argument('-s', '--source', default='gcs',
                         choices=['gcs', 'usgs'],
                         help='Source service for tar')
    aparser.add_argument('-c', '--clean', action='store_true',
                         help='clean up all intermediate files')
    aparser.add_argument('-v', '--verbose', action='store_true',
                         help='Report details on progress.')
    aparser.add_argument('scene',
                         help='Scene name, ie. LC82301202013305LGN00')
    return aparser

def main(rawargs):
    args = get_parser().parse_args(rawargs)
    process(args.source, args.scene,
            verbose = args.verbose,
            clean = args.clean)

if __name__ == '__main__':
    status = main(sys.argv[1:])
    sys.exit(status)
