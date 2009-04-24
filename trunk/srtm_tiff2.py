#!/usr/bin/python
"""
Provides an interface to SRTM elevation data stored in GeoTIFF Files.

Only class srtm_tiff is defined in this module.

"""
import sys
import fileinput
from math import floor
from optparse import OptionParser
import re
import gdal, gdalnumeric

class srtm_tiff:
    """
    Provides an interface to SRTM elevation data stored in GeoTIFF files.
    
    Suitable files are available from http://srtm.csi.cgiar.org/.
    The file srtm_tiff.txt should contain the filenames of the GeoTIFF
    files to be used - one per line, followed by a white space separated
    bounding box - N S E W, and the width and height of each pixel (in deg).
    The bounding box can be generated from a simple list of filenames by
    doing the following on the command line:
       python ./srtm_tiff2.py -f <infile> --index
    This will produce a file <infile>.out which is the same as infile, but with
    the indexing information added.

    For testing you can do:
       python ./srtm_tiff2.py -f <infile> --lat=<lat> --lon=<lon>

       python ./srtm_tiff2.py -h
    gives more information on arguments.

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
    
    def __init__(self,fname,verbose,debug):
        """Reads the GeoTIFF files into memory ready for processing.

        The tiles are stored as a list of dictionaries containing the
        data for each tile (one dictionary per tile) - self.tilearr.
        The structure of the dictionary is described in the loadTile()
        documentation.

        The list of files to be read is taken from srtm_tiff.txt unless
        the filename is specified as a parameter to __init__.

        """
        self.verbose = verbose
        self.debug = debug
        if self.debug:
            print "DEBUG: Debug output selected - forcing verbose output too"
            self.verbose = True
        self.tilearr = []

        if (self.verbose):
            print "Reading Tile Data List from %s" % fname
      
        for line in fileinput.input(fname):
            line=line.rstrip("\n")
            # Uses special case of split so that consecutive white space
            # is ignored = using ' ' gives lots of empty strings...
            if (self.debug):
                print "line=%s." % line
                
            (fname,N,S,E,W,lat_pixel,lon_pixel) = line.split(None,6)  
            filedict = {}
            filedict['fname']=fname
            filedict['N']=float(N)
            filedict['S']=float(S)
            filedict['E']=float(E)
            filedict['W']=float(W)
            filedict['lat_pixel']=float(lat_pixel)
            filedict['lon_pixel']=float(lon_pixel)
            self.tilearr.append(filedict)
            
        if (self.debug):
            print "init finished"



    def getTileIndex(self,lat,lon):
        """return the index number (in self.tilearr of the tile containing
        point (lat,lon).

        This is not intended as a public function - I can't think of what
        use it would be to anyone - use getElevation(lat,lon) instead.
        It searches through the list of tile dictionaries to find the one
        containing the requested point.  An error (-999) is returned if
        none of the available tiles contains the desired location.

        """
        for i in range(len(self.tilearr)):
            td = self.tilearr[i]
            fname = td["fname"]
            N = td["N"]
            S = td["S"]
            E = td["E"]
            W = td["W"]
            if (self.debug):
                print "N=%s S=%s E=%s W=%s point=(%s,%s)" % (N,S,E,W,lat,lon)
            if ((lat<=N and lat>=S) and (lon<=E and lon>=W)):
                if (self.verbose):
                    print "point (%s, %s) fits in bounding box %s (%s,%s %s,%s)" % \
                      (lat,lon,i,N,W,S,E)
                return i
            else:
                if (self.debug):
                    print "point (%s, %s) DOES NOT FIT in bounding box \
                    (%s,%s %s,%s)" % \
                    (lat,lon,N,W,S,E)
        if (self.verbose):
            print "oh no -data out of bounds - point = (%s,%s)" % (lat,lon)
        return(-999)


    def getElevation(self,lat,lon,bilinear=False):
        """Returns the elevation in metres of point (lat,lon).
        Uses bilinar interpolation to interpolate the SRTM data to the
        required point if bilinear=True, otherwise uses single point.

        An error (-999) is returned if the location is not covered by any
        of the loaded tiles.

        """
        tdi = self.getTileIndex(lat,lon)
        td = self.tilearr[tdi]
        fname = td['fname']
        if (tdi == -999):
            print "Error (%s,%s) out of Range." % (lat,lon)
            return -999
        else:
            dataset = gdal.Open(fname)
            (row,col) = self.posFromLatLon(lat,lon, td)
            if (self.verbose):
                print "row=%s, col=%s" % (row,col)
            if (bilinear):
                if (self.debug):
                    print "Using bilinear interpolation to find height"
                htarr=gdalnumeric.DatasetReadAsArray(dataset,col,row,2,2)
                if (self.debug):
                    print htarr
                height = bilinearInterpolation(htarr[0][0],
                                               htarr[0][1],
                                               htarr[1][0],
                                               htarr[1][1],
                                               lat, lon)
            else:
                if (self.debug):
                    print "Using single point to get height"
                htarr=gdalnumeric.DatasetReadAsArray(dataset,col,row,1,1)
                height = htarr[0][0]
            return height
         
        return -999

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

def bilinearInterpolation(tl, tr, bl, br, a, b):
  # GJ Shamelessly plagiarised from route_altitude_profile/trunk/server/altitude.py
  # In the likely case that the coordinate is somewhere between
  # grid points, we will apply bilinear interpolation.

  # http://en.wikipedia.org/wiki/Bilinear_interpolation

  # We will use the simplest formula.

  # return (1.0 - a) * (1.0 - b) * tl + a * (1.0 - b) * tr + (1.0 -a) * b * bl + a * b * br

  b1 = tl
  b2 = bl - tl
  b3 = tr - tl
  b4 = tl - bl - tr + br

  return b1 + b2 * a + b3 * b + b4 * a * b


def getBBox(fname):
    """Open GeoTIFF file fname and return its bounding box
    (N,S,E,W) and its pixel height and with (lat_pixel,lon_pixel) in degrees.
    
    """
    dataset = gdal.Open(fname)
    geotransform = dataset.GetGeoTransform()
    xsize = dataset.RasterXSize
    ysize = dataset.RasterYSize
    lon_origin = geotransform[0]
    lat_origin = geotransform[3]
    lon_pixel = geotransform[1]
    lat_pixel = geotransform[5]
    N = lat_origin
    S = lat_origin + ysize*lat_pixel
    E = lon_origin + xsize*lon_pixel
    W = lon_origin
    return (N,S,E,W,lat_pixel,lon_pixel)


def indexTiles(*args):
    """ Determine the bounding boxes of each data file listed in the
    text file args[0].
    
    If no argument given, uses the default "srmt_tiff.txt".
    Writes the bounding boxes back to the file for future use.
    """
    tilelist = []
    if len(args) != 0: 
        fname = args[0]
    else:
        fname = "srtm_tiff.txt"

    if (self.verbose):
        print "Reading Tile Data List from %s" % fname
        
    for line in fileinput.input(fname):
        tilefname=line.rstrip("\n")
        if tilefname.find(' ') != -1:
            (tilefname,rhs) = tilefname.split(' ',1)

        if (self.verbose):
            print "Indexing File %s." % tilefname
        bbox = getBBox(tilefname)
        tilestring = "%s %10.6f %10.6f %10.6f %10.6f %10.8f %10.8f\n" % \
                     (tilefname, bbox[0], bbox[1], bbox[2], bbox[3], \
                      bbox[4], bbox[5])
        if (self.verbose):
            print "tilestring = %s." % tilestring
        tilelist.append(tilestring)

    fileinput.close()

    outfname = "%s.out" % fname
    if (self.verbose):
        print "Writing indexed file to %s." % outfname
    f = open(outfname,'w')
    for str in tilelist:
        f.write(str)
    f.close()




if __name__ == '__main__':            
    parser = OptionParser()
    usage = "srtm_tiff2 [options]"
    parser.add_option("-f", "--file", dest="filename",
                      help="name of file containing list of srtm data files",
                      metavar="FILE")
    parser.add_option("-i", "--index", action="store_true",dest="index",
                      help="Index the input file to contain bounding box information")
    parser.add_option("--lat", dest="lat",
                      help="latitude of point")
    parser.add_option("--lon", dest="lon",
                      help="longitude of point")
    parser.add_option("-b", "--bilinear", action="store_true",dest="bilinear",
                      help="Include verbose output")
    parser.add_option("-v", "--verbose", action="store_true",dest="verbose",
                      help="Include verbose output")
    parser.add_option("-d", "--debug", action="store_true",dest="debug",
                      help="Include debug output")
    parser.set_defaults(filename="srtm_tiff.txt",
                        lat="54",
                        lon="-1",
                        bilinar=False,
                        debug=False,
                        verbose=False)
    (options,args)=parser.parse_args()

    if (options.debug):
        print options
        print args

    if options.index:
        print "Indexing....%s" % options.filename
        indexTiles(options.filename)
        print "done"

    
                
    srtm = srtm_tiff(options.filename,options.verbose,options.debug)
    lat = float(options.lat)
    lon = float(options.lon)
    ele = srtm.getElevation(lat,lon,options.bilinear)
    if (options.bilinear):
        print "WARNING!!!!!:  Although this prints an answer, it doesn't work!!!"
    print "Elevation of point (%s,%s) is %d\n\n" % (lat,lon,ele)

  
