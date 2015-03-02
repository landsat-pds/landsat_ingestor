import os

BUCKET_NAME = 'landsat-pds'
BUCKET_URL = 'https://s3-us-west-2.amazonaws.com/landsat-pds'

ACCESS_ID = os.environ.get('LANDSAT_PDS_ACCESS_ID',None)
ACCESS_KEY = os.environ.get('LANDSAT_PDS_ACCESS_KEY',None)

if ACCESS_ID is None or ACCESS_KEY is None:
    print
    print 'WARNING: Missing one or both of LANDSAT_PDS_ACCESS_ID and '
    print '         LANDSAT_PDS_ACCESS_KEY environment variables.'
    print
