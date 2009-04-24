"""
NAME: GPX Parse
DESC:  A simple class to parse a GPX file.
HISTORY:  06aug2008  GJ  Plagiarised from 
                         http://code.activestate.com/recipes/528877/

"""

import sys, string
from xml.dom import minidom, Node

class GPXParser:
    def __init__(self, gpxStr):
        print "GPXParser.__init__()"
        self.tracks = {}
        self.routes = {}
        try:
            doc = minidom.parseString(gpxStr)
            doc.normalize()
        except:
            return # handle this properly later
        gpx = doc.documentElement
        for node in gpx.getElementsByTagName('rte'):
            print "reading route"
            self.parseRoute(node)
        for node in gpx.getElementsByTagName('trk'):
            self.parseTrack(node)
        print("init finished")

    def parseRoute(self, rte):
        print "parseRoute()"
        rteName = rte.getElementsByTagName('name')[0].firstChild.data
        if not rteName in self.routes:
            self.routes[rteName] = []
        for rtept in rte.getElementsByTagName('rtept'):
            lat = float(rtept.getAttribute('lat'))
            lon = float(rtept.getAttribute('lon'))
            ptName = rtept.getElementsByTagName('name')[0].firstChild.data
            print "read point %s at (%s,%s)" % (ptName,lat,lon)
            self.routes[rteName].append({'lat':lat,'lon':lon,'name':ptName})

    def getRoute(self, rteName):
        "Return a list of route points (lat,lon,name) for route rteName"
        return [(point['lat'],point['lon'],point['name'])
                for point in self.routes[rteName]]



    def parseTrack(self, trk):
        name = trk.getElementsByTagName('name')[0].firstChild.data
        if not name in self.tracks:
            self.tracks[name] = {}
        for trkseg in trk.getElementsByTagName('trkseg'):
            for trkpt in trkseg.getElementsByTagName('trkpt'):
                lat = float(trkpt.getAttribute('lat'))
                lon = float(trkpt.getAttribute('lon'))
                ele = float(trkpt.getElementsByTagName('ele')[0].firstChild.data)
                rfc3339 = trkpt.getElementsByTagName('time')[0].firstChild.data
                self.tracks[name][rfc3339]={'lat':lat,'lon':lon,'ele':ele}

    def getTrack(self, name):
        times = self.tracks[name].keys()
        points = [self.tracks[name][time] for time in times.sort()]
        return [(point['lat'],point['lon']) for point in points]
