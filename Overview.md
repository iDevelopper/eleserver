# Introduction #

EleServer is a simple web application to provide data on ground elevation
above sea level.  It uses Shuttle Radio Topograpy Mission (SRTM) data obtained
from [srtm.csi.cgiar.org](http://srtm.csi.cgiar.org)

Eleserver can be used in two ways:
  * he simplest way is to use a HTTP GET request, providing lat and lon as parameters, and eleserver retrns the height of the point in metres above sea level.

  * he second way is to use a HTTP POST request to send a GPX file to the server.  The GPX file should contain a route (ie not a track log). The server will list the points in the route, with their altitudes.

The next development is to sort out the interface a bit better so that
eleserver can easily be called from JavaScript, so I can interface it
with my GPX route editor at
http://maps.webhop.net maps.webhop.net

Note that the route
editor needs some work too - in particular it uses the MultiMap API and I
want to change it to OpenLayers.  Local file acces in JavaScript is also messy,
so you have to paste the GPX file into a text area...

# Usage #

  * http://maps.webhop.net:1281 - returns this page.
  * http://maps.webhop.net:1281?lat=XXXX&lon=YYYY - returns a single value, which is the elevation of the particular point in metres above sea level.
  * POST a GPX file (tagged as 'GPXFile' to http://maps.webhop.net:1281 - it returns a list of the route points in the file, with elevations.
  * It also tries to plot route profiles, but I can't remember how - will have to read the code...

# Links #
  * See CodeStructure for details of the structure of the code.
  * Get SRTM Data from http://srtm.csi.cgiar.org
  * An alternative to EleServer is http://wiki.openstreetmap.org/index.php/Route_altitude_profiles_SRTM