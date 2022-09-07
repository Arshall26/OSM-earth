# Methods to convert latitude/longitude coordinates to Web Mercator projection (EPSG:3857) and vice versa.
#
# We are aware of the existence of the pyproj interface but for reasons
# of code portability in another language (C++), we wanted to use the conversion formulas.

import math

# Ellipsoid model constant (actual value here is for WGS84)
sm = 6378137

# Convert lat/lon coordinates (degree or radian) to Web Mercator projection. Considers the coordinates given in radian by default.
def latLonToWebMercator(lat, lon, isDeg=False):
    if isDeg:
        lat = degToRad(lat)
        lon = degToRad(lon)

    x = sm * lon
    y = sm * math.log((math.sin(lat)+1)/math.cos(lat))

    return x,y

# Convert Web Mercator coordinates to lat/lon coordinates (degree or radian). Output coordinates in radian by default.
def webMercatorToLatLon(x, y, degOutput=False):
    lon = x/sm
    r = math.sqrt(math.exp(2*y/sm) + 1)
    theta = math.asin(1/r)
    lat = math.acos(1/r) - theta

    if degOutput:
        lat = radToDeg(lat)
        lon = radToDeg(lon)

    return lat, lon

# Convert degree to radian
def degToRad(deg):
    return (deg / 180.0 * math.pi)

# Convert radian to degree
def radToDeg(rad):
    return (rad * 180.0 / math.pi)