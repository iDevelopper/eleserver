# Introduction #

The code is written in Python.  It uses the GDAL library python bindings from http://www.gdal.org to read the SRTM GeoTiff Files.

# Directory Structure #
The python files should be in a single directory.  I like to have a sub-directory called 'data' to store the SRTM GeoTiff files, but this is not essential.

The file srtm\_tiff.txt contains a list of GeoTiff files to be used, along with bounding box data.


# Python Files #
  * eleserver.py - Main program, which does the web server bits.
  * srtm\_tiff.py - A class that will read a number of SRTM GeoTiff files and provides functions to access them.
  * gpx\_parse.py - a GPX file parser, which is used to process route data.
  * do\_plot.py - a class to plot data to produce png files.

  * srtm\_tiff2.py and srtm\_tiff3.py are different versions of srtm\_tiff.py, which use different methods of dealing with the GeoTiff files.
