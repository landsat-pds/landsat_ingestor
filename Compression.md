TIFF Compression
================

One goal when serving the landsat8 data from S3 is to avoid users having to download a compress tar file with all the bands, and extract just what they want from that.  In fact, I'd like the dataset to be directly exploitable in a variety of ways:

 - scripts that fetch by http as part of an ingestion flow.
 - mounting the whole bucket as a file system on EC2 instances
 - accessing an individual file directly by GDAL's chunk oriented /vsicurl/ 
 - browsing the bucket as a http web tree (like a file system on a web server)

I'd still like to make use of compression to reduce storage volumes, and
transport volumes. 

One approach is just to compress each of the individual files with something
like GZIP, BZIP2, etc.  That could be built into the name, and the client is
just responsible for uncompressing it.  With appropriate mimetypes browsers
would actually understand this nature and could do it transparently.

Another approach would be to use compression within the TIFF files themselves.
This means the files *are* compressed on cloud storage, and during delivery,
but even naive clients (curl, etc) would get a resulting file, and decompression
only needs to be done when a client image viewer, processor accesses the pixels.

Here we try to explore some of the tradeoffs in compression.

```
$ ls -lh
total 429M
-rw-rw-r-- 1 warmerdam warmerdam  47M Dec 17 11:17 b1_deflate_pred2_bigblock.tif
-rw-rw-r-- 1 warmerdam warmerdam  49M Dec 17 11:15 b1_deflate_pred2.tif
-rw-rw-r-- 1 warmerdam warmerdam  45M Dec 17 11:16 b1_deflate_pred2_tiled.tif
-rw-rw-r-- 1 warmerdam warmerdam  57M Dec 17 11:14 b1_deflate.tif
-rw-rw-r-- 1 warmerdam warmerdam  37M Dec 17 11:14 b1.tif.bz2
-rw-rw-r-- 1 warmerdam warmerdam  57M Dec 17 11:14 b1.tif.gz
-rw-rw-r-- 1 warmerdam warmerdam 140M Dec 17 11:13 LC82301202013305LGN00_B1.TIF
```



Minimizing Metadata Effects
---------------------------

A downside of doing in-file compression is tha we are no longer deliverying
the exact same bytes originally offered by USGS.  It is easy to ensure that
the pixel values are exactly the same, but it is harder to ensure that the
metadata (TIFF tags, GeoTIFF tags, etc) are exactly the same. 


Before as reported by gdalinfo:
```
$ gdalinfo LC82301202013305LGN00_B1.TIF 
Driver: GTiff/GeoTIFF
Files: LC82301202013305LGN00_B1.TIF
Size is 8531, 8581
Coordinate System is:
PROJCS["PS         WGS84",
    GEOGCS["WGS 84",
        DATUM["WGS_1984",
            SPHEROID["WGS 84",6378137,298.257223563,
                AUTHORITY["EPSG","7030"]],
            AUTHORITY["EPSG","6326"]],
        PRIMEM["Greenwich",0],
        UNIT["degree",0.0174532925199433],
        AUTHORITY["EPSG","4326"]],
    PROJECTION["Polar_Stereographic"],
    PARAMETER["latitude_of_origin",-71],
    PARAMETER["central_meridian",0],
    PARAMETER["scale_factor",1],
    PARAMETER["false_easting",0],
    PARAMETER["false_northing",0],
    UNIT["metre",1,
        AUTHORITY["EPSG","9001"]]]
Origin = (-795915.000000000000000,-533085.000000000000000)
Pixel Size = (30.000000000000000,-30.000000000000000)
Metadata:
  AREA_OR_POINT=Point
Image Structure Metadata:
  INTERLEAVE=BAND
Corner Coordinates:
Upper Left  ( -795915.000, -533085.000) (123d48'47.66"W, 81d12' 0.12"S)
Lower Left  ( -795915.000, -790515.000) (134d48'17.90"W, 79d42' 7.89"S)
Upper Right ( -539985.000, -533085.000) (134d37'53.70"W, 83d 1'28.66"S)
Lower Right ( -539985.000, -790515.000) (145d39'49.67"W, 81d12'20.12"S)
Center      ( -667950.000, -661800.000) (134d44' 6.05"W, 81d21'42.03"S)
Band 1 Block=8531x1 Type=UInt16, ColorInterp=Gray
```

After as reported by gdalinfo:
```
$ gdalinfo b1_deflate.tif 
Driver: GTiff/GeoTIFF
Files: b1_deflate.tif
Size is 8531, 8581
Coordinate System is:
PROJCS["PS         WGS84",
    GEOGCS["WGS 84",
        DATUM["WGS_1984",
            SPHEROID["WGS 84",6378137,298.257223563,
                AUTHORITY["EPSG","7030"]],
            AUTHORITY["EPSG","6326"]],
        PRIMEM["Greenwich",0],
        UNIT["degree",0.0174532925199433],
        AUTHORITY["EPSG","4326"]],
    PROJECTION["Polar_Stereographic"],
    PARAMETER["latitude_of_origin",-71],
    PARAMETER["central_meridian",0],
    PARAMETER["scale_factor",1],
    PARAMETER["false_easting",0],
    PARAMETER["false_northing",0],
    UNIT["metre",1,
        AUTHORITY["EPSG","9001"]]]
Origin = (-795915.000000000000000,-533085.000000000000000)
Pixel Size = (30.000000000000000,-30.000000000000000)
Metadata:
  AREA_OR_POINT=Point
Image Structure Metadata:
  COMPRESSION=DEFLATE
  INTERLEAVE=BAND
Corner Coordinates:
Upper Left  ( -795915.000, -533085.000) (123d48'47.66"W, 81d12' 0.12"S)
Lower Left  ( -795915.000, -790515.000) (134d48'17.90"W, 79d42' 7.89"S)
Upper Right ( -539985.000, -533085.000) (134d37'53.70"W, 83d 1'28.66"S)
Lower Right ( -539985.000, -790515.000) (145d39'49.67"W, 81d12'20.12"S)
Center      ( -667950.000, -661800.000) (134d44' 6.05"W, 81d21'42.03"S)
Band 1 Block=8531x1 Type=UInt16, ColorInterp=Gray
```

