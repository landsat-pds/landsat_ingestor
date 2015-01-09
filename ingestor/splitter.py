#!/usr/bin/env python

import sys
import os

def run_command(cmd, verbose=False):
    if verbose:
        print cmd
        
    result = os.system(cmd)

    if result != 0:
        raise Exception('command "%s" failed with code %d.' % (cmd, result))

def internally_compress(filename, verbose=False):
    wrk_file = filename.rsplit('.',1)[0] + '_wrk.tif'

    run_command(
        'gdal_translate %s %s %s -co COMPRESS=DEFLATE -co PREDICTOR=2' % (
            filename,
            wrk_file, 
            '' if verbose else '-q'),
        verbose=verbose)

    # Check?

    os.unlink(filename)
    os.rename(wrk_file, filename)
    

def split(root_scene, filename, verbose=False):
    # Returns name of unpack directory will have a root named according
    # to the scene_root.
    
    tgt_dir = root_scene
    assert not os.path.exists(tgt_dir)

    os.mkdir(tgt_dir)
    
    # Unpack tar file, GCS .tars are bz2 and require -j flag.
    run_command(
        'tar x%s%sf %s --directory=%s ' % (
          'j' if filename.endswith('.bz') else '',
          'v' if verbose else '',
          filename, tgt_dir),
        verbose=verbose)

    # add some confirmation expected files were extracted.

    for filename in os.listdir(tgt_dir):
        if filename.endswith('.TIF'):
            internally_compress(os.path.join(tgt_dir, filename),
                                verbose = verbose)

    return tgt_dir
    

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print 'Usage: splitter.py <root_scene> <compressed_tar_file>'
        sys.exit(1)

    print split(sys.argv[1], sys.argv[2], verbose=True)

    
