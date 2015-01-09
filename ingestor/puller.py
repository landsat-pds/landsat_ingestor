#!/usr/bin/env python

import argparse
import sys
import pprint

import puller_gcs
import puller_usgs


def pull(source, scene_root, scene_dict, verbose=False):
    if source == 'gcs':
        return puller_gcs.pull(scene_root, scene_dict, verbose=verbose)
    elif source == 'usgs':
        return puller_usgs.pull(scene_root, scene_dict, verbose=verbose)
    else:
        raise Exception('Landsat source "%s" not recognised.' % source)

def get_parser():
    aparser = argparse.ArgumentParser(
        description='Pull Landsat scene from source')

    aparser.add_argument('-s', '--source', default='usgs',
                         choices=['gcs', 'usgs'],
                         help='Source service for tar')
    aparser.add_argument('scene',
                         help='Scene name, ie. LC82301202013305LGN00')
    return aparser

def main(rawargs):
    args = get_parser().parse_args(rawargs)
    scene_dict = {}
    filename = pull(args.source, args.scene, scene_dict, verbose=True)

    print 'Filename:', filename
    pprint.pprint(scene_dict)

if __name__ == '__main__':
    status = main(sys.argv[1:])
    sys.exit(status)
