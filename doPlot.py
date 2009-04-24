#!/usr/bin/python

"""Produce a PNG image of a simple XY chart

"""
from math import *
import matplotlib
matplotlib.use('Agg')  # Need to do this to avoid X11/GTK errors in pylab
import pylab

def doPlot(srtm,points,fname):
    """Produce a PNG Image of a simple XY chart

    How it works:
    x_rtepts and y_rtepts are lists of x and y values to plot with symbols
    - these are the locations of the specified route points.
    x_prof and y_prof are lists of x and y values to plot as a line -
    these are the intermediate heights between the route points.
    This version just plots 10 points between each route point (set by nProf).

    """
    nProf = 10  # The number of height profile points between each route point.

    ptNo=1
    x_rtepts = []
    y_rtepts = []

    x_prof = []
    y_prof = []

    isfirst = 1
    for pt in points:
       x_rtepts.append(ptNo)
       y_rtepts.append(srtm.getElevation(pt[0],pt[1]))

       if (isfirst == 1):
           prevlat = pt[0]
           prevlon = pt[0]
           prevpt = pt
           isfirst = 0
       else:
           for n in range(0,nProf):
               xp = ptNo-1 + float(n)/nProf
               #print "n=%d: nProf=%d n/nProf=%s xp=%s" % \
               (n,nProf,float(n)/nProf,xp)
               #print "n=%d: prevpt[0]=%s, pt[0]=%s" % (n,prevpt[0],pt[0])
               lat = prevpt[0] + (pt[0]-prevpt[0])*n/nProf 
               lon = prevpt[1] + (pt[1]-prevpt[1])*n/nProf
               dist = distance(prevlat,prevlon,lat,lon)
               prevlat = lat
               prevlon = lon
               x_prof.append(xp)
               #x_prof.append(dist)
               y_prof.append(srtm.getElevation(lat,lon))
           prevpt = pt
       ptNo += 1
           

    pylab.plot(x_rtepts,y_rtepts,'ro',
               x_prof,y_prof,'b-')
    pylab.savefig(fname)
    pylab.show()

def distance(lat1_deg,lon1_deg, lat2_deg,lon2_deg):
    """Calculate the distance between two (lat,lon) points.

    Borrowed from http://www.sethoscope.net/geophoto/

    """
    pi = 3.14159265358979
    lat1=lat1_deg * pi / 180
    lat2=lat2_deg * pi / 180
    lon1=lon1_deg * pi / 180
    lon2=lon2_deg * pi / 180
    # http://en.wikipedia.org/wiki/Great-circle_distance
    # Of the several formula listed, this one retains the most accuracy at short distances
    dist = atan(sqrt(pow(cos(lat2)*sin(abs(lon1-lon2)),2) + pow(cos(lat1)*sin(lat2) - sin(lat1)*cos(lat2)*cos(lon1-lon2),2)) / (sin(lat1)*sin(lat2) + cos(lat1)*cos(lat2)*cos(lon1-lon2)))
    dist *= 6372795 # convert from radians to meters
    return dist





    
