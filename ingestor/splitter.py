#!/usr/bin/env python

import sys
import os


def split(root_scene, filename):
    # Returns name of unpack directory will have a root named according
    # to the scene_root.
    
    tgt_dir = root_scene
    assert not os.path.exists(tgt_dir)

    os.mkdir(tgt_dir)
    
    # Currently assuming .bz tar file, but we can check this later if
    # USGS or other sources are packaged differently than GCS.

    cmd = 'tar --directory=%s xjvf %s ' % (tgt_dir, filename)
    print cmd
    
    os.system(cmd)

    # add some confirmation expected files were extracted.

    return tgt_dir
    

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print 'Usage: splitter.py <root_scene> <compressed_tar_file>'
        sys.exit(1)

    print split(sys.argv[1], sys.argv[2])

    
