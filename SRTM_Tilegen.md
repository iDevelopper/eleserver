# Introduction #
srtm\_tilegen.py is a utility to generate SlippyMap tiles from SRTM data that give a background colour that varies with altitude.  The idea is to use them as a background for maps that are not rendered with elevation contours.
It creates a directory tree containing png images that can be read directly as OpenLayers TMS tiles.


# Details #
srtm\_tilegen.py uses the same GEOTIFF files as eleserver, so requires a file srtm\_tiff.txt to describe which files to read into memory.

The program takes a slippymap tile ID which is specified as a starting point, (x,y) at a specified zoom level, z.
It creates a 256x256 pixel image to represent the tile.  The colour of each pixel is chosen based on the elevation of the land at the pixel.  If the elevation is negative the pixel is blue, as areas of sea are usually represented by negative elevations.

The same process is repeated to produce higher zoom level tiles beneath the start tile, until the zoom level reaches the maximum zoom level specified, when the program terminates.

Add your content here.  Format your content with:
  * Text in **bold** or _italic_
  * Headings, paragraphs, and lists
  * Automatic links to other wiki pages