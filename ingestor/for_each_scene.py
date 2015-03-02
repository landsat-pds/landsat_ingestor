#!/usr/bin/env python

import sys
import os
import argparse

import pusher

def for_each_scene(script, prefix='L8/'):

    dirs_for_prefix = {}

    count = 0
    for path in pusher.list(prefix):
        if path.endswith('_MTL.txt'):
            os.system('%s %s' % (script, os.path.dirname(path)))
            count += 1

    print 'Processed %d scenes.' % count


def get_parser():
    aparser = argparse.ArgumentParser(
        description='Loop over all scenes applying a script.')

    aparser.add_argument('-p', '--prefix',
                         default='L8',
                         help='Prefix to search, ie --prefix=L8/011/022, default is L8')
    aparser.add_argument('script', nargs='?',
                         default = 'echo',
                         help='Script name to run, taking the s3 path as an argument.')

    return aparser

def main(rawargs):
    args = get_parser().parse_args(rawargs)
    for_each_scene(args.script, prefix=args.prefix)

if __name__ == '__main__':
    status = main(sys.argv[1:])
    sys.exit(status)
