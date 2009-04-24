#!/usr/bin/python
"""
Provides an interface to SRTM elevation data stored in GeoTIFF Files.

Only class srtm_tiff is defined in this module.

"""
import sys
import fileinput
import random
from math import floor
from time import clock
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
    
    MaxOpenFiles = 10
    NumOpenFiles = 0

    def __init__(self,fname,maxfiles,verbose,debug):
        """Reads the GeoTIFF files into memory ready for processing.

        The tiles are stored as a list of dictionaries containing the
        data for each tile (one dictionary per tile) - self.tilearr.
        The structure of the dictionary is:
        - filedict['fname']     - file name of this GeoTIFF File.
        - filedict['N']         - The northern most latitude covered by this file
        - filedict['S']         - The southern most latitude covered by this file
        - filedict['E']         - The eastern most ....
        - filedict['W']         - The western most ....
        - filedict['lat_pixel'] - the vertical size (in deg Lat) of each pixel.
        - filedict['lon_pixel'] - the horizontal size (in deg Lon) of each pixel.
        - filedict['handle']    - the file handle of the file (if open) or -1 if not open.

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
                
            (fname,N,S,E,W,lat_pixel,lon_pixel,xsize,ysize) = line.split(None,8)  
            filedict = {}
            filedict['fname']=fname
            filedict['N']=float(N)
            filedict['S']=float(S)
            filedict['E']=float(E)
            filedict['W']=float(W)
            filedict['lat_pixel']=float(lat_pixel)
            filedict['lon_pixel']=float(lon_pixel)
            filedict['xsize'] = int(xsize)
            filedict['ysize'] = int(ysize)
            filedict['handle']=-1
            self.tilearr.append(filedict)

        self.MaxOpenFiles = int(maxfiles)
        self.NumOpenFiles = 0

        if (self.verbose):
            print "init finished - MaxOpenFiles = %s" % self.MaxOpenFiles



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


    def closeAFile(self):
        """
        Close one of the open GeoTiff Files, and update NumOpenFiles
        accordingly.
        """
        if (self.debug):
            print "closeAFile - NumOpenFiles = %s" % self.NumOpenFiles
        if (self.NumOpenFiles <= 0):
            print "closeAFile() - Error - NumOpenFiles = %s:  Doing Nothing" % \
                      self.NumOpenFiles
            return -1
        fileno = random.randint(1, self.NumOpenFiles)
        if (self.debug):
            print "Closing open file number %s" % fileno

        openFileCount = 0
        for i in range(len(self.tilearr)):
            td = self.tilearr[i]
            if (td['handle']!=-1):
                openFileCount += 1
                if (self.debug):
                    print "Found File Number %s" % openFileCount
                if (openFileCount == fileno):
                    if (self.debug):
                        print "Closing File %s" % td['fname']
                    #gdal.close(td['handle'])
                        del self.tilearr[i]['handle']
                        self.tilearr[i]['handle'] = -1
                    self.NumOpenFiles -= 1
        
    

    def getElevation(self,lat,lon,bilinear=False):
        """Returns the elevation in metres of point (lat,lon).
        Uses bilinar interpolation to interpolate the SRTM data to the
        required point if bilinear=True, otherwise uses single point.

        An error (-999) is returned if the location is not covered by any
        of the loaded tiles.

        """
        tdi = self.getTileIndex(lat,lon)
        if (tdi == -999):
            if (self.verbose):
                print "Error (%s,%s) out of Range." % (lat,lon)
            return -999
        else:
            td = self.tilearr[tdi]
            fname = td['fname']
            """ 
            If the required file is not open, open it.
            But if we are already have the maximum number of files open,
            we have to close one first
            """
            if (td['handle'] == -1):
                if (self.debug):
                    print "Required file is closed"
                if (self.NumOpenFiles >= self.MaxOpenFiles):
                    if (self.debug):
                        print "Maximum number of open files reached - closing one first"
                    self.closeAFile()
                else:
                    if (self.debug):
                        print "Number of open files ok - NumOpenFiles = %s, MaxOpenFiles=%s" % \
                            (self.NumOpenFiles, self.MaxOpenFiles)
                if (self.debug):
                    print "Opening file %s" % fname
                td['handle'] = gdal.Open(fname)
                self.NumOpenFiles += 1
                if (self.debug):
                    print "NumOpenFiles = %s" % self.NumOpenFiles
            else:
                if (self.debug):
                    print "File already open - NumOpenFiles = %s" % self.NumOpenFiles
            (row,col) = self.posFromLatLon(lat,lon, td)
            if (self.verbose):
                print "row=%s, col=%s" % (row,col)
            if (bilinear):
                if (self.debug):
                    print "Using bilinear interpolation to find height"
                htarr=gdalnumeric.DatasetReadAsArray(td['handle'],col,row,2,2)
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
                htarr=gdalnumeric.DatasetReadAsArray(td['handle'],col,row,1,1)
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
        xsize = td["xsize"]
        ysize = td["ysize"]
        
        rowno = int(floor((lat-N)/lat_pixel))
        colno = int(floor((lon-W)/lon_pixel))

        # Error checking to correct any rounding errors.
        if (rowno<0):
            rowno = 0
        if (rowno>(xsize-1)):
            rowno = xsize-1
        if (colno<0):
            colno = 0
        if (colno>(ysize-1)):
            colno = xsize-1
            
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
    (N,S,E,W) and its pixel height and with (lat_pixel,lon_pixel) in degrees and the
    size of the image in pixels (xsize, ysize).
    
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
    return (N,S,E,W,lat_pixel,lon_pixel,xsize,ysize)


def indexTiles(fname,verbose, debug):
    """ Determine the bounding boxes of each data file listed in the
    text file args[0].
    
    If no argument given, uses the default "srmt_tiff.txt".
    Writes the bounding boxes back to the file for future use.
    """
    tilelist = []
    if (verbose):
        print "Reading Tile Data List from %s" % fname
        
    for line in fileinput.input(fname):
        tilefname=line.rstrip("\n")
        if tilefname.find(' ') != -1:
            (tilefname,rhs) = tilefname.split(' ',1)

        if (verbose):
            print "Indexing File %s." % tilefname
        bbox = getBBox(tilefname)
        tilestring = "%s %17.15f %17.15f %17.15f %17.15f %17.15f %17.15f %d %d\n" % \
                     (tilefname, bbox[0], bbox[1], bbox[2], bbox[3], \
                      bbox[4], bbox[5], bbox[6], bbox[7])
        print "width=%s, height=%s" % (bbox[4],bbox[5])
        if (verbose):
            print "tilestring = %s." % tilestring
        tilelist.append(tilestring)

    fileinput.close()

    outfname = "%s.out" % fname
    if (verbose):
        print "Writing indexed file to %s." % outfname
    f = open(outfname,'w')
    for str in tilelist:
        print str
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
    parser.add_option("--maxfiles", dest="maxfiles",
                      help="maximum number of open files")
    parser.add_option("-b", "--bilinear", action="store_true",dest="bilinear",
                      help="Use bilinear interpolation to improve accuracy (slower)")
    parser.add_option("-t", "--test", action="store_true",dest="test",
                      help="Run a series of self tests")
    parser.add_option("--bigtest",dest="bigtest",
                      help="Run the specified number of test cases to check speed")
    parser.add_option("-v", "--verbose", action="store_true",dest="verbose",
                      help="Include verbose output")
    parser.add_option("-d", "--debug", action="store_true",dest="debug",
                      help="Include debug output")
    parser.set_defaults(filename="srtm_tiff.txt",
                        lat="54",
                        lon="-1",
                        maxfiles="10",
                        bilinear=False,
                        test=False,
                        bigtest=0,
                        debug=False,
                        verbose=False)
    (options,args)=parser.parse_args()

    if (options.debug):
        options.verbose = True
        print options
        print args

    if options.index:
        print "Indexing....%s" % options.filename
        indexTiles(options.filename,options.verbose,options.debug)
        print "Warning - note that I did not overwrite your input file."
        print "          This means you have to do it manually!!!!"
    else:
    
                
        srtm = srtm_tiff(options.filename,options.maxfiles,options.verbose,options.debug)



        if (options.bigtest != 0):
            options.test = True

            if (options.test == False):
                lat = float(options.lat)
                lon = float(options.lon)
                ele = srtm.getElevation(lat,lon,options.bilinear)
                if (options.bilinear):
                    print "WARNING!!!!!:  Although this prints an answer, it doesn't work!!!"
                    print "Elevation of point (%s,%s) is %d\n\n" % (lat,lon,ele)
            else:
                print "Test Cases"
                testcases = ( (54, -1), (54, -2), (54, -3), \
                                  (53,-1), (53,-2), (53,-3), \
                                  (52,-1), (52,-2), (52,-3), \
                                  #                          (51,-1), (51,-2), (51,-3), \
                                  #                          (50,-1), (50,-2), (50,-3), \
                                  #                          (59,-6), (59,-7), (59,-8), \
                                  #                          (54,-6), (54,-7), (54,-8), \
                                  #                          (59,-1), (59,-2), (59,-3), \
                                  (54,1), (54,2), (54,3) \
                                  #                          (49,-1), (49,-2), (49,-3) \
                                  )
                print testcases
                for case in testcases:
                    (lat,lon) = case
                    print "lat=%s lon=%s" % (lat,lon)
                    ele = srtm.getElevation(lat,lon,options.bilinear)
                    print "Elevation of point (%s,%s) is %d\n\n" % (lat,lon,ele)
                        
                if (options.bigtest != 0):
                    numtests = int(options.bigtest)
                    print "Running Time Test - numtests=%s" % numtests
                    tstart = clock()
                    print "tstart=%s" % tstart
                    for i in range(1, numtests):
                        lat = random.uniform(50,60)
                        lon = random.uniform(-10, 5)
                        ele = srtm.getElevation(lat,lon,options.bilinear)
                        
                        
                    tend = clock()
                    print "tend=%s" % tend
                    total_ms = 1000.*(tend-tstart)
                    timePerTest = total_ms / numtests
                    print "Total time = %s ms" % (total_ms)
                    print "Time per elevation measurement = %s ms" % timePerTest
