#!/usr/bin/env python

import argparse
import sys
import os
import shutil
import pprint
import requests

import puller
import splitter
import thumbnailer
import pusher
import scene_info
import index_maker

def process(source, scene_root, verbose=False):

    s3_path = 'tarq/%s.tar.gz' % scene_root
    if pusher.check_file_existance(s3_path):
        raise Exception('%s already exists!' % s3_path)

    scene_dict = {}
    local_tarfile = puller.pull(source, scene_root, scene_dict,
                                verbose=verbose)
    pusher.push_file(local_tarfile, s3_path, verbose=verbose)
    os.unlink(local_tarfile)
    
def get_parser():
    aparser = argparse.ArgumentParser(
        description='Copy the tar file for one scene from usgs to our S3 tar queue.')

    aparser.add_argument('-s', '--source', default='usgs',
                         choices=['gcs', 'usgs', 'auto', 's3'],
                         help='Source service for tar')
    aparser.add_argument('-v', '--verbose', action='store_true',
                         help='Report details on progress.')
    aparser.add_argument('scene',
                         help='Scene name, ie. LC82301202013305LGN00')
    return aparser

def main(rawargs):
    args = get_parser().parse_args(rawargs)
    process(args.source, args.scene, verbose = args.verbose)


if __name__ == '__main__':
    status = main(sys.argv[1:])
    sys.exit(status)
