#!/usr/bin/env python

import sys
import os
import pprint
import datetime
import logging

import mtlutils

CSV_FIELDS = [
    'entityId',
    'acquisitionDate',
    'cloudCover',
    'processingLevel',
    'path',
    'row',
    'min_lat',
    'min_lon',
    'max_lat',
    'max_lon',
    'download_url']

def make_scene_line(scene_dict):

    line = ''
    for fieldname in CSV_FIELDS:
        value = str(scene_dict.get(fieldname,''))
        line += value + ','

    # strip off extra comma
    line = line[:-1]

    return line

def append_scene_line(filename, scene_dict):
    if not os.path.exists(filename):
        init_list_file(filename)
        
    # This may be expensive to do often, but should be plenty fast when
    # we are just adding one new recently processed scene.
    open(filename,'a').write(make_scene_line(scene_dict)+'\n')
    
def init_list_file(filename):
    open(filename,'w').write((','.join(CSV_FIELDS)) + '\n')

def split_scene_line(line):
    fields = line.strip().split(',')

    scene_dict = {}
    for i in range(len(fields)):
        scene_dict[CSV_FIELDS[i]] = fields[i]

    return scene_dict


def add_mtl_info(scene_dict, scene_root, scene_dir):
    mtl_filename = '%s/%s_MTL.txt' % (scene_dir, scene_root)
    mtl_dict = mtlutils.parsemeta(mtl_filename)

    # Strip useless level of indirection.
    mtl_dict = mtl_dict['L1_METADATA_FILE']
    
    scene_dict['entityId'] = scene_root

    acq_datetime = datetime.datetime.combine(
        mtl_dict['PRODUCT_METADATA']['DATE_ACQUIRED'],
        mtl_dict['PRODUCT_METADATA']['SCENE_CENTER_TIME'])
    scene_dict['acquisitionDate'] = str(acq_datetime)
        
    scene_dict['cloudCover'] = mtl_dict['IMAGE_ATTRIBUTES']['CLOUD_COVER']
    scene_dict['processingLevel'] = mtl_dict['PRODUCT_METADATA']['DATA_TYPE']
    scene_dict['path'] = mtl_dict['PRODUCT_METADATA']['WRS_PATH']
    scene_dict['row'] = mtl_dict['PRODUCT_METADATA']['WRS_ROW']

    lats = [mtl_dict['PRODUCT_METADATA']['CORNER_LL_LAT_PRODUCT'],
            mtl_dict['PRODUCT_METADATA']['CORNER_LR_LAT_PRODUCT'],
            mtl_dict['PRODUCT_METADATA']['CORNER_UL_LAT_PRODUCT'],
            mtl_dict['PRODUCT_METADATA']['CORNER_UL_LAT_PRODUCT']]
    lons = [mtl_dict['PRODUCT_METADATA']['CORNER_LL_LON_PRODUCT'],
            mtl_dict['PRODUCT_METADATA']['CORNER_LR_LON_PRODUCT'],
            mtl_dict['PRODUCT_METADATA']['CORNER_UL_LON_PRODUCT'],
            mtl_dict['PRODUCT_METADATA']['CORNER_UL_LON_PRODUCT']]
        
    scene_dict['min_lat'] = min(lats)
    scene_dict['max_lat'] = max(lats)
    scene_dict['min_lon'] = min(lons)
    scene_dict['max_lon'] = max(lons)
    
    return scene_dict

if __name__ == '__main__':

    if len(sys.argv) < 3:
        print 'Usage: scene_info.py <root_scene> <scene_dir_path>'
        sys.exit(1)

    scene_dict = {}
    add_mtl_info(scene_dict, sys.argv[1], sys.argv[2])

    pprint.pprint(scene_dict)
    print make_scene_line(scene_dict)
