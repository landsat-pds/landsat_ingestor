#!/usr/bin/env python

import sys
import os
import numpy
import pprint

import pusher

def make_index(s3_path='L8', verbose=False):

    dirs_for_prefix = {}

    for path in pusher.list(s3_path):
        components = path.split('/')[:4]

        rpath = components[0]
        for c in components[1:]:
            if c == 'index.html':
                continue

            l = dirs_for_prefix.get(rpath,[])
            if c not in l:
                l.append(c)
            dirs_for_prefix[rpath] = l
            rpath += '/' + c

    index_updates = 0
    for path in dirs_for_prefix.keys():
        files = ''
        for filename in dirs_for_prefix[path]:
            files += '<li><a href="%s/index.html">%s</a></li>\n' % (filename, filename)
        
        src_dir = os.path.dirname(__file__)
        doc = open(src_dir + '/tree_index_template.html').read()
        doc = doc.replace('@@@TITLE@@@', path)
        doc = doc.replace('@@@FILES@@@', files)

        open('index.html','w').write(doc)
        
        index_path = path + '/index.html'
        if verbose:
            print 'Update %s with %d files.' % (
                index_path, len(dirs_for_prefix[path]))

        pusher.push_file('index.html', index_path, overwrite=True)
        index_updates += 1

    print 'Updated %d index.html files under %s.' % (index_updates, s3_path)

if __name__ == '__main__':

    make_index()

    
