#!/usr/bin/env python

import argparse
import sys

import puller_gcs


def pull(source, scene_root, verbose=False):
    if source == 'gcs':
        return puller_gcs.pull(scene_root, verbose=verbose)
    else:
        raise Exception('Landsat source "%s" not recognised.' % source)

def get_parser():
    aparser = argparse.ArgumentParser(
        description='Pull Landsat scene from source')

    aparser.add_argument('-s', '--source', default='gcs',
                         choices=['gcs', 'usgs'],
                         help='Source service for tar')
    aparser.add_argument('scene',
                         help='Scene name, ie. LC82301202013305LGN00')
    return aparser

def main(rawargs):
    args = get_parser().parse_args(rawargs)
    filename = pull(args.source, args.scene, verbose=True)

    print 'Filename:', filename

if __name__ == '__main__':
    status = main(sys.argv[1:])
    sys.exit(status)
