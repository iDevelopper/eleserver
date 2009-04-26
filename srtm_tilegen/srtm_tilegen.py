#!/usr/bin/python


from optparse import OptionParser
from tilenames import *
from srtm_tiff import srtm_tiff
import gd
import os


def rendertile(options,srtm,tile_X,tile_Y,Z):
    nw_latlon=xy2latlon(tile_X,tile_Y,Z)
    se_latlon=xy2latlon(tile_X+1,tile_Y+1,Z)

    print "nw corner of tile is %f, %f" % nw_latlon
    print "sw corner of tile is %f, %f" % se_latlon

    im = gd.image((256, 256))
    white = im.colorAllocate((255, 255, 255))
    black = im.colorAllocate((0,0,0))
    blue  = im.colorAllocate((0,0,255))
    im.colorTransparent(white)
    im.interlace(1)

    tileoutdir = "%s/%d/%d" % (options.outputdir,Z,tile_X)
    print "tileoutdir=%s" % tileoutdir
    if not os.path.isdir(tileoutdir):
        os.makedirs(tileoutdir)

    fname = "%s/%d.png" % (tileoutdir,tile_Y)

    # NOTE = we only render the tile if it does not exist!!!
    #
    if os.path.isfile(fname):
        print "%s exists already - skipping..." % fname
    else:
        for px_x in range (0, 256):
            for px_y in range(0,256):
                px_X = tile_X + px_x/256.
                px_Y = tile_Y + px_y/256.
                px_latlon = xy2latlon(px_X,px_Y,Z)
                ele = srtm.getElevation(px_latlon[0],px_latlon[1])
                colval = 255-int(255.0*ele/500.0)
                if (options.debug): 
                    print "px=(%d,%d), latlon=(%f,%f), ele=%f, colval=%d" % \
                        (px_x,px_y,px_latlon[0],px_latlon[1],ele,colval)
                if (ele<0):
                    im.setPixel((px_x,px_y),blue)
                else:
                    im.setPixel((px_x,px_y),im.colorResolve((0,colval,0)))
        f=open(fname,"w")
        im.writePng(f)
        f.close()

    # If we have not got down to the maximum zoom level,
    # Render the next zoom level down (4 sub tiles beneath the current one).
    if Z<int(options.maxzoom):
        print "Z=%s, options.maxzoom=%s - rendering next layer..." % \
            (Z,options.maxzoom)
        rendertile(options,srtm,2*tile_X,2*tile_Y,Z+1)
        rendertile(options,srtm,2*tile_X+1,2*tile_Y,Z+1)
        rendertile(options,srtm,2*tile_X,2*tile_Y+1,Z+1)
        rendertile(options,srtm,2*tile_X+1,2*tile_Y+1,Z+1)


def srtm_tilegen(options):
    print "srtm_tilegen: options=%s" % options
    print "Requested Tile is X=%s, Y=%s, Z=%s" % \
        (options.x, options.y, options.z)

    tile_X = int(options.x)
    tile_Y = int(options.y)
    Z = int(options.z)

    srtm = srtm_tiff()

    rendertile(options,srtm,tile_X,tile_Y,Z)


if __name__ == '__main__':            
    parser = OptionParser()
    usage = "srtm_tilegen [options]"
    parser.add_option("-f", "--file", dest="filename",
                      help="name of file containing list of srtm data files",
                      metavar="FILE")
    parser.add_option("-x",dest="x",
                      help="Tile X coordinate")
    parser.add_option("-y",dest="y",
                      help="Tile X coordinate")
    parser.add_option("-z",dest="z",
                      help="Tile zoom level")
    parser.add_option("-o",dest="outputdir",
                      help="Output Directory for tiles")
    parser.add_option("-m",dest="maxzoom",
                      help="Maximum Zoom Level to Render")
    parser.add_option("-t", "--test", action="store_true",dest="test",
                      help="Run a series of self tests")
    parser.add_option("--bigtest",dest="bigtest",
                      help="Run the specified number of test cases to check speed")
    parser.add_option("-v", "--verbose", action="store_true",dest="verbose",
                      help="Include verbose output")
    parser.add_option("-d", "--debug", action="store_true",dest="debug",
                      help="Include debug output")

# Roseberry Topping is:
#   http://d.tah.openstreetmap.org/Tiles/maplint/14/8141/5221.png
# Hartlepool is 2034, 1301, Z12
    parser.set_defaults(filename="srtm_tiff.txt",
#                        x = 2034,
#                        y = 1301,
#                        z = 12,
                        x=2034,
                        y=1301,
                        z = 12,
                        outputdir = "./tiles",
                        maxzoom = 17,
                        test=False,
                        bigtest=0,
                        debug=False,
                        verbose=False)
    (options,args)=parser.parse_args()

    if (options.debug):
        options.verbose = True
        print options
        print args

    srtm_tilegen(options)

    print("Done")
