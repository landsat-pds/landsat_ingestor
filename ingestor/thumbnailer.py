#!/usr/bin/env python

import sys
import os
import numpy

from osgeo import gdal, gdal_array

TAIL_TRIM = 0.01

def get_band(filename, target_percent):
    ds = gdal.Open(filename)
    xsize = int(ds.RasterXSize * target_percent / 100.0)
    ysize = int(ds.RasterYSize * target_percent / 100.0)
    image = ds.GetRasterBand(1).ReadAsArray(resample_alg = gdal.GRIORA_Average,
                                            buf_xsize = xsize,
                                            buf_ysize = ysize)
    return image

def get_scale(image):
    '''
    Return the values at which to clip an image.
    '''
    histogram = numpy.histogram(image, 65536, (-0.5, 65535.5))[0]

    # Clear the nodata:
    histogram[:1] = 0

    count = numpy.sum(histogram)

    # Walk up the near-black side of the histogram until
    # we reach the end of the first percentile:
    counter = 0
    scale_min = None
    for i in range(len(histogram)):
        counter += histogram[i]
        if counter > count * TAIL_TRIM:
            scale_min = i
            break

    # Same, but moving left from the white end:
    counter = 0
    scale_max = None
    for i in range(len(histogram)-1, 0, -1):
        counter += histogram[i]
        if counter > count * TAIL_TRIM:
            scale_max = i
            break

    return scale_min, scale_max

def scale_image(image, scale_min, scale_max):
    '''
    Take a (presumptively uint16) image and return it scaled into 
    a uint8 image stretched linearly so that scale_min is mapped
    to 0 and scale_max is mapped to 255.
    '''
    image = image.astype('float32')
    image = (255 * (image - scale_min) / (scale_max - scale_min))
    image = numpy.maximum(0, numpy.minimum(255, image))
    image = image.astype('uint8')
    return image

def thumbnail(root_scene, scene_dir, verbose=False):
    red_file = '%s/%s_B4.TIF' % (scene_dir, root_scene)
    grn_file = '%s/%s_B3.TIF' % (scene_dir, root_scene)
    blu_file = '%s/%s_B2.TIF' % (scene_dir, root_scene)

    if not os.path.exists(red_file) or not os.path.exists(grn_file) \
            or not os.path.exists(blu_file):
        print 'Missing one or more of %s, %s and %s, skip thumbnailing.' % (
            red_file, grn_file, blu_file)
        return

    large_thumbnail = numpy.array([
        get_band(red_file, 15),
        get_band(grn_file, 15),
        get_band(blu_file, 15)])
    
    small_thumbnail = numpy.array([
        get_band(red_file, 3),
        get_band(grn_file, 3),
        get_band(blu_file, 3)])

    # Set the scale values for both images from the larger one:
    scale_min, scale_max = get_scale(large_thumbnail)
    
    large_thumbnail = scale_image(large_thumbnail, scale_min, scale_max)
    small_thumbnail = scale_image(small_thumbnail, scale_min, scale_max)

    # TODO: Georeference these jpegs
    gdal_array.SaveArray(
        large_thumbnail,
        '%s/%s_thumb_large.jpg' % (scene_dir, root_scene),
        format = 'JPEG')

    gdal_array.SaveArray(
        small_thumbnail,
        '%s/%s_thumb_small.jpg' % (scene_dir, root_scene),
        format = 'JPEG')

    for filename in os.listdir(scene_dir):
        if filename.endswith('.aux.xml'):
            os.unlink(os.path.join(scene_dir,filename))
    

if __name__ == '__main__':

    if len(sys.argv) < 3:
        print 'Usage: thumbnailer.py <root_scene> <scene_dir_path>'
        sys.exit(1)

    thumbnail(sys.argv[1], sys.argv[2])

    
