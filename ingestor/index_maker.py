#!/usr/bin/env python

import sys
import os
import numpy


def make_index(scene_root, scene_dir, verbose=False):

    title = scene_root

    files = ''
    for filename in os.listdir(scene_dir):
        if 'thumb' in filename:
            continue
        if filename == 'index.html':
            continue

        files += '<li><a href="%s">%s</a></li>\n' % (filename, filename)
        
    src_dir = os.path.dirname(__file__)
    doc = open(src_dir + '/index_template.html').read()
    doc = doc.replace('@@@TITLE@@@', title)
    doc = doc.replace('@@@FILES@@@', files)
    doc = doc.replace('@@@SCENE_ROOT@@@', scene_root)
    open(scene_dir + '/index.html','w').write(doc)

if __name__ == '__main__':

    if len(sys.argv) < 3:
        print 'Usage: index_maker.py <scene_root> <scene_dir_path>'
        sys.exit(1)

    make_index(sys.argv[1], sys.argv[2])

    
