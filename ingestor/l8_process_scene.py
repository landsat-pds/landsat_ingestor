#!/usr/bin/env python

import argparse
import sys

import puller
import splitter
import thumbnailer
import pusher

def process(source, scene_root):
    if pusher.check_existance(scene_root):
        print 'Scene %s already exists on destination bucket.' % scene_root
        
    local_tarfile = puller.pull(source, scene_root)
    local_dir = splitter.split(scene_root, local_tarfile)
    thumbnailer.thumbnail(scene_root, local_dir)
    pusher.push(scene_root, local_dir)
    

def get_parser():
    aparser = argparse.ArgumentParser(
        description='Process one Landsat scene from source to S3.')

    aparser.add_argument('-s', '--source', default='gcs',
                         choices=['gcs', 'usgs'],
                         help='Source service for tar')
    aparser.add_argument('scene',
                         help='Scene name, ie. LC82301202013305LGN00')
    return aparser

def main(rawargs):
    args = get_parser().parse_args(rawargs)
    process(args.source, args.scene)

if __name__ == '__main__':
    status = main(sys.argv[1:])
    sys.exit(status)
