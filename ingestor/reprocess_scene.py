#!/usr/bin/env python

import sys
import os
import argparse
import shutil

import pusher
import splitter
import scene_index_maker

from osgeo import gdal

def fix_tiling(scene_root, files, verbose=False):
    ret = False
    for filename in files:
        if not filename.endswith('.TIF'):
            continue

        ds = gdal.Open(filename)
        bx, by = ds.GetRasterBand(1).GetBlockSize()
        ds = None
        
        if by != 1:
            continue

        ret = True
        
        splitter.internally_compress(filename, verbose=verbose)

    return ret

def fix_pyramid(scene_root, files, verbose=False):
    ret = False
    for filename in files:
        if not filename.endswith('.TIF'):
            continue

        ds = gdal.Open(filename)
        ov_count = ds.GetRasterBand(1).GetOverviewCount()
        ds = None

        if ov_count != 0:
            continue
        
        ret = True
        
        splitter.build_pyramid(filename, verbose=verbose)

    return ret

def fix_index(scene_root, scene_dir, verbose=False):

    index_filename = scene_dir + '/index.html'
    
    old_index = open(index_filename).read()

    scene_index_maker.make_index(scene_root, scene_dir, verbose=verbose)

    new_index = open(index_filename).read()

    return new_index != old_index

def reprocess(scene_root, local_path, verbose=False):

    files = [os.path.join(local_path,x) for x in os.listdir(local_path)]

    ret = False

    ret |= fix_tiling(scene_root, files, verbose=verbose)
    ret |= fix_pyramid(scene_root, files, verbose=verbose)
    ret |= fix_index(scene_root, local_path, verbose=verbose)

    if verbose:
        if ret:
            print 'Changes made, re-upload'
        else:
            print 'No changes made.'

    return ret

def get_parser():
    aparser = argparse.ArgumentParser(
        description='Reprocess a local, or s3 Landsat8 scene.')

    aparser.add_argument('-v', '--verbose', action='store_true',
                         help='Generate verbose output')
    aparser.add_argument('--s3-path',
                         help='Path on S3 to scene, ie. L8/011/022/LC8011022201509LGN00')
    aparser.add_argument('--local-path',
                         help='Path to local directory for local update.')

    return aparser

def main(rawargs):
    args = get_parser().parse_args(rawargs)

    if args.s3_path is not None:
        scene_root = os.path.basename(args.s3_path)
        args.local_path = scene_root
        pusher.pull_scene(scene_root, args.local_path, verbose=args.verbose)

    else:
        if args.local_path is None:
            print 'ERROR: Please specify one of --s3-path or --local-path'
            sys.exit(1)
        scene_root = os.path.basename(args.local_path)
        
    upload = reprocess(scene_root, args.local_path, verbose=args.verbose)

    if upload and args.s3_path:
        scene_dict = {}
        pusher.push(scene_root, args.local_path, scene_dict,
                    verbose=args.verbose, overwrite=True)

    if args.s3_path:
        shutil.rmtree(args.local_path)


if __name__ == '__main__':
    status = main(sys.argv[1:])
    sys.exit(status)
