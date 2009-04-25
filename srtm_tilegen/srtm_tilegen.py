#!/usr/bin/python


from optparse import OptionParser
from tilenames import *
from srtm_tiff import srtm_tiff
import gd




def srtm_tilegen(options):
    print "srtm_tilegen: options=%s" % options
    print "Requested Tile is X=%d, Y=%d, Z=%d" % \
        (options.x, options.y, options.z)

    tile_X = options.x
    tile_Y = options.y
    Z = options.z

    srtm = srtm_tiff()


    nw_latlon=xy2latlon(tile_X,tile_Y,Z)
    se_latlon=xy2latlon(tile_X+1,tile_Y+1,Z)

    print "nw corner of tile is %f, %f" % nw_latlon
    print "sw corner of tile is %f, %f" % se_latlon

    im = gd.image((256, 256))
    white = im.colorAllocate((255, 255, 255))
    black = im.colorAllocate((0,0,0))
    im.colorTransparent(white)
    im.interlace(1)


    for px_x in range (0, 256):
        for px_y in range(0,256):
            px_X = tile_X + px_x/256.
            px_Y = tile_Y + px_y/256.
            px_latlon = xy2latlon(px_X,px_Y,Z)
            ele = srtm.getElevation(px_latlon[0],px_latlon[1])
            colval = int(255.0*ele/500.0)
            #print "px=(%d,%d), latlon=(%f,%f), ele=%f, colval=%d" % \
            #    (px_x,px_y,px_latlon[0],px_latlon[1],ele,colval)

#            im.setPixel((px_x,px_y),im.colorAllocate((colval,colval,colval)))
            if (ele<200.):
                im.setPixel((px_x,px_y),white)
            else:
                im.setPixel((px_x,px_y),black)

    f=open("xx.png","w")
    im.writePng(f)
    f.close()


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
    parser.set_defaults(filename="srtm_tiff.txt",
#                        x = 8141,
#                        y = 5221,
#                        z = 14,
                        x=2035,
                        y=1305,
                        z = 12,
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
