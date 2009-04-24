#!/usr/bin/python
#----------------------------------------------------------------------------
# Elevation data server
#
# Features:
#   * Serves SRTM elevation data in response to HTTP GET Requests
#   * Expects two parameters lat and lon which are the lattitude and
#     longitude of the point for which height data is required.
#----------------------------------------------------------------------------
# Author: Graham Jones, using the pyrender server.py by Oliver White as the 
# starting point (http://wiki.openstreetmap.org/index.php/Pyrender).
# Added the POST processing code using the example from:
#  http://fragments.turtlemeat.com/pythonwebserver.php
#
# Daemon code plagiarised from
#  http://homepage.hispeed.ch/py430/python/daemon.py
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#---------------------------------------------------------------------------
from BaseHTTPServer import *
import re
import sys
import os
import string,cgi,time
from srtm_tiff import srtm_tiff
from gpx_parse import GPXParser
from doPlot import doPlot

LOGFILE = '/var/log/eleserver.log'
PIDFILE = '/var/run/eleserver.pid'
WDIR = '/home/disk2/OSM/eleserver'
class Log:
    """file like for writes with auto flush after each write
    to ensure that everything is logged, even during an
    unexpected exit."""
    def __init__(self, f):
        self.f = f
        
    def write(self, s):
        self.f.write(s)
        self.f.flush()


class eleServer(BaseHTTPRequestHandler):
    "Basic Land Elevation Web Server"
  
    def makeSessionID(self,st):
	import md5, time, base64
	m = md5.new()
	m.update('this is a test of the emergency broadcasting system')
	m.update(str(time.time()))
	m.update(str(st))
	return string.replace(base64.encodestring(m.digest())[:-3], '/', '$')

    def return_file(self, filename, contentType='text/HTML'):
        "Serve a real file from disk (for indexes etc.)"
        f = open(filename, "r")
        if(f):
            self.send_response(200)
            self.send_header('Content-type',contentType) # TODO: more headers
            self.end_headers()
            self.wfile.write(f.read())
            f.close()
        else:
            self.send_response(404)

    def showMessage(self,message):
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()
        self.wfile.write(message)

    def showUsageError(self):
        "Display an error message in the web browser"
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()
        self.wfile.write('-1 - ERROR: You must specify both lat=value ' \
                         'and lon=value as parameters to the GET Request')

    def do_GET(self):
        "process http GET requests - get elevation of a single (lat,lon) point."
        # See if any arguments have been passed by checking for a '?' in the URL.
        if self.path.find('?') != -1: 
            (self.path, self.query_string) = self.path.split('?', 1)
            print "self.query_string=%s." % (self.query_string)

            # Separate the arguments into a dictionary of key=value pairs.
            argDict = self.parseGetArgs(self.query_string)
            if "lat" in argDict:
                lat = float(argDict["lat"])
            else:
                self.showUsageError()
                return
            if "lon" in argDict:
                lon = float(argDict["lon"])
            else:
                self.showUsageError()
                return

            ele = srtm.getElevation(lat,lon)
            if (ele != -999):
                if (ele == -32768):
                    ele = 0
                message = '%s - Elevation of (lat=%s, lon=%s) is %s m\n' % (ele, lat, lon, ele)
                self.showMessage(message)
            else:
                message = '-1 - ERROR: (lat=%s, lon=%s) is out of range\n' % (lat, lon)
                self.showMessage(message)
            print "lat=%f, lon=%f, ele=%f\n" % (lat,lon,ele)

        else:
            # if no parameters, return main html page.
            if self.path=='/':
                self.return_file('eleserver.html')
                return
            else:
                (lhs,rhs) = self.path.split("/",1)
                print "Returning File %s - cwd=%s" % (rhs, os.getcwd());
                self.return_file(rhs)
        
######################################################################

    def do_POST(self):
        """Process HTTP POST Requests
  
        Accepts a file uploaded via a POST request, and parses it as a
        GPX file containing route points.
        Returns a table of the route point locations and elevations
        
        """
        print "sessionID = %s " % self.makeSessionID('test');
        global rootnode
        print "do_POST()"
        try:
            ctype, pdict = cgi.parse_header(  \
                           self.headers.getheader('content-type'))
            if ctype == 'multipart/form-data':
                print "multipart/form-data"
                query=cgi.parse_multipart(self.rfile, pdict)
#                self.send_response(301)
#                self.end_headers()
                if query.has_key('GPXFile'):
                    upfilecontent = query.get('GPXFile')
                    parser = GPXParser(upfilecontent[0])
                    points = parser.getRoute('route')
                    if query.has_key('Plot'):
                        fname = 'doPlot.png'
                        doPlot(srtm,points,fname);
                        #self.return_file(fname)
                        msg = '<a href=\"%s\">%s<\a>' % \
                                         (fname,fname)
                        self.showMessage(msg)
                        print msg
                        
                    else:
                        for pt in points:
                            linestr = "Point=%s (%s,%s) - Ele=%s<br>" % \
                                      (pt[2],pt[0],pt[1],srtm.getElevation(pt[0],pt[1]))
                            print linestr
                            self.wfile.write(linestr)
                else:
                    self.wfile.write("Error - No data labelled GPXFile provided")
            else:
                print "ctype = %s, but I need multipart/form-data" % ctype
        except :
            print "do_Post() - ERROR!!! ", sys.exc_info()[0]
            raise

  ##############################################################################  # NAME: parseGetArgs(queryString)
        # DESC: queryString should be a series of key=value pairs, separated by '&'
  #       characters (as per http GET requests).
  #       Returns a dictionary of dict["key"]=value data.
  # HIST: 03Aug2008 GJ ORIGINAL VERSION
  #
  #
    def parseGetArgs(self,queryString):
        'Parse a HTTP GET Query String into a dictionary of key, value pairs'
        argList = {}
        qs = queryString
        #    print "parseGetArgs: qs=%s" % (qs)
        while (len(qs)>0):
            if qs.find('&') != -1:
                (kvp,rhs) = qs.split('&',1)
                qs = rhs
            else:
                kvp = qs
                qs=''
            if kvp.find('=') != -1:
                (key,val) = kvp.split('=',1)
                argList[key]=val
            else:
                print "parseGetArgs Error - key but no = sign? %s" % queryString
        return argList
    #return argList





############################################################################

def main():
    os.chdir(WDIR)
    sys.stdout = sys.stderr = Log(open(LOGFILE, 'a+'))
    os.setegid(103)
    os.seteuid(103)
    print "eleserver.main() - cwd=%s" % (os.getcwd())
    
    try:
        server = HTTPServer(('',1281), eleServer)
        global srtm
        srtm=srtm_tiff()
        print "Starting web server. Open http://localhost:1281 to access EleServer."
        server.serve_forever()
    except KeyboardInterrupt:
        server.socket.close()
        sys.exit()

if __name__ == "__main__":
    # do the UNIX double-fork magic, see Stevens' "Advanced
    # Programming in the UNIX Environment" for details (ISBN 0201563177)
    try:
        pid = os.fork()
        if pid > 0:
            # exit first parent
            sys.exit(0)
    except OSError, e:
        print >>sys.stderr, "fork #1 failed: %d (%s)" % (e.errno, e.strerror)
        sys.exit(1)

    # decouple from parent environment
    os.chdir("/")   #don't prevent unmounting....
    os.setsid()
    os.umask(0)

    # do second fork
    try:
        pid = os.fork()
        if pid > 0:
            # exit from second parent, print eventual PID before
            #print "Daemon PID %d" % pid
            open(PIDFILE,'w').write("%d"%pid)
            sys.exit(0)
    except OSError, e:
        print >>sys.stderr, "fork #2 failed: %d (%s)" % (e.errno, e.strerror)
        sys.exit(1)

    # start the daemon main loop
    main()


