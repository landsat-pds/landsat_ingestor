#!/bin/bash

set -o errexit

sudo apt-get install git parallel gdal-bin python-gdal
#sudo pip install requests
#sudo pip install boto

if [ ! -d usgs ] ; then
  git clone git@github.com:mapbox/usgs.git
  (cd usgs; sudo python setup.py install)
fi

#if [ ! -d pygaarst ] ; then
#  git clone git@github.com:chryss/pygaarst
#fi

