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

        filesize = os.path.getsize(os.path.join(scene_dir,filename))

        if filesize > 100000:
            nice_size = ' (%.1fMB)' % (filesize / 1048576.0)
        else:
            nice_size = ' (%.1fKB)' % (filesize / 1024.0)

        files += '<li><a href="%s">%s</a>%s</li>\n' % (
            filename, filename, nice_size)
        
    src_dir = os.path.dirname(__file__)
    doc = open(src_dir + '/index_template.html').read()
    doc = doc.replace('@@@TITLE@@@', title)
    doc = doc.replace('@@@FILES@@@', files)
    doc = doc.replace('@@@SCENE_ROOT@@@', scene_root)
    open(scene_dir + '/index.html','w').write(doc)

if __name__ == '__main__':

    if len(sys.argv) < 3:
        print 'Usage: scene_index_maker.py <scene_root> <scene_dir_path>'
        sys.exit(1)

    make_index(sys.argv[1], sys.argv[2])

    
