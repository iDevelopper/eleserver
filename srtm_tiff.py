#!/usr/bin/python
"""
Provides an interface to SRTM elevation data stored in GeoTIFF Files.

Only class srtm_tiff is defined in this module.

"""
import sys
import fileinput
from math import floor
import re
import gdal, gdalnumeric

class srtm_tiff:
    """
    Provides an interface to SRTM elevation data stored in GeoTIFF files.
    
    Suitable files are available from http://srtm.csi.cgiar.org/.
    The file srtm_tiff.txt should contain the filenames of the GeoTIFF
    files to be used - one per line.

    To use this class do:
        from srtm_tiff import srtm_tiff
        srtm = srtm_tiff()
        lat=54
        lon=-1
        ele = srtm.getElevation(lat,lon)

    The pulic functions of this class are:
        __init__ the constructor, called as srtm_tiff()
        getElevation(lat,lon)
        
    """
    
    def __init__(self,*args):
        """Reads the GeoTIFF files into memory ready for processing.

        The tiles are stored as a list of dictionaries containing the
        data for each tile (one dictionary per tile) - self.tilearr.
        The structure of the dictionary is described in the loadTile()
        documentation.

        The list of files to be read is taken from srtm_tiff.txt unless
        the filename is specified as a parameter to __init__.

        """
        self.tilearr = []
        if len(args) != 0: 
            fname = args[0]
        else:
            fname = "srtm_tiff.txt"
            print "Reading Tile Data List from %s" % fname
      
        for line in fileinput.input(fname):
            line=line.rstrip("\n")
            (tilefname,rhs) = line.split(None,1)  

            print "Loading File %s." % tilefname
            td = self.loadTile(tilefname)
            self.tilearr.append(td)

        print "init finished"


    def getTileData(self,lat,lon):
        """return the tiledata dictionary of the tile containing point
        (lat,lon).

        This is not intended as a public function - I can't think of what
        use it would be to anyone - use getElevation(lat,lon) instead.
        It searches through the list of tile dictionaries to find the one
        containing the requested point.  An error (-999) is returned if
        none of the loaded tiles contains the desired location.

        """
        for td in self.tilearr:
            N = td["N"]
            S = td["S"]
            E = td["E"]
            W = td["W"]
            #print "N=%s S=%s E=%s W=%s point=(%s,%s)" % (N,S,E,W,lat,lon)
            if ((lat<=N and lat>=S) and (lon<=E and lon>=W)):
                #print "point (%s, %s) fits in bounding box (%s,%s %s,%s)" % \
                #      (lat,lon,N,W,S,E)
                return td
            else:
                pass
                #print "point (%s, %s) DOES NOT FIT in bounding box \
                #(%s,%s %s,%s)" % \
                #(lat,lon,N,W,S,E)
        print "oh no -data out of bounds - point = (%s,%s)" % (lat,lon)
        return(-999)


    def getElevation(self,lat,lon):
        """Returns the elevation in metres of point (lat,lon).

        An error (-999) is returned if the location is not covered by any
        of the loaded tiles.

        """
        td = self.getTileData(lat,lon)
        if (td == -999):
            print "Error (%s,%s) out of Range." % (lat,lon)
            return -999
        else:
            tilevals = td["data"]
            (row,col) = self.posFromLatLon(lat,lon, td)
            height = tilevals[row][col]
            return height
        return -999


    def loadTile(self,filename):
        """
        Loads a GeoTIFF tile from disk and returns a dictionary containing
        the file data, plus metadata about the tile.

        The dictionary returned by this function contains the following data:
            xsize - the width of the tile in pixels.
            ysize - the height of the tile in pixels.
            lat_origin - the latitude of the top left pixel in the tile.
            lon_origin - the longitude of the top left pixel in the tile.
            lat_pixel - the height of one pixel in degrees latitude.
            lon_pixel - the width of one pixel in degrees longitude.
            N, S, E, W - the bounding box for this tile in degrees.
            data - a two dimensional array containing the tile data.

        """
        dataset = gdal.Open(filename)
        geotransform = dataset.GetGeoTransform()
        xsize = dataset.RasterXSize
        ysize = dataset.RasterYSize
        lon_origin = geotransform[0]
        lat_origin = geotransform[3]
        lon_pixel = geotransform[1]
        lat_pixel = geotransform[5]
        retdict = {}
        retdict["xsize"]=xsize
        retdict["ysize"]=ysize
        retdict["lat_origin"]=lat_origin
        retdict["lon_origin"]=lon_origin
        retdict["lat_pixel"]=lat_pixel
        retdict["lon_pixel"]=lon_pixel
        retdict["N"]=lat_origin
        retdict["S"]=lat_origin + lat_pixel*ysize
        retdict["E"]=lon_origin + lon_pixel*xsize
        retdict["W"]=lon_origin
        retdict["data"]=gdalnumeric.DatasetReadAsArray(dataset)
        return retdict


    def posFromLatLon(self,lat,lon,td):
        """Converts coordinates (lat,lon) into the appropriate (row,column)
        position in the GeoTIFF tile data stored in td.

        This does not do any error checking - it assumes that (lat,lon) is
        within the tile.  This is because td should be set by
        getTileData(lat,lon), which selects the correct tile, or returns
        an error if we do not have a tile containing the requested position.
        
        """
        N = td["N"]
        S = td["S"]
        E = td["E"]
        W = td["W"]
        lat_pixel = td["lat_pixel"]
        lon_pixel = td["lon_pixel"]
        
        rowno = int(floor((lat-N)/lat_pixel))
        colno = int(floor((lon-W)/lon_pixel))
        return (rowno,colno)


if __name__ == '__main__':            
    srtm = srtm_tiff();
    print "srtm_tiff.py"
    print "Number of Arguments=%s\n" % len(sys.argv)
  
    if (len(sys.argv)!=3):
        print "Usage: strm_tiff.py lat lon\n\n"
    else:
        lat = float(sys.argv[1])
        lon = float(sys.argv[2])
        print "point is (%s,%s)\n" % (lat,lon)  
        ele = srtm.getElevation(lat,lon)
        print "Elevation is %d\n\n" % (ele)

  
