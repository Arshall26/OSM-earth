# Program which use Géoservices image tile API.
#
# The file name format of the recorded image is as follows:
# imageTopLeftLat_imageTopLeftLon_imageBottomRightLat_imageBottomRightLon_dataType_zoomLevel.jpeg
#
# API's documentation: https://geoservices.ign.fr/documentation/services/api-et-services-ogc/images-tuilees-wmts-ogc
#
# NB: Lat/lon coordinates (decimal degrees) given in input and output are rounded to 6 decimal places.
#     At 6 decimal places, the last number represents 0.111 meters in latitude 
#     and a maximum of 0.111 meters in longitude at the equator (the precision increases as you approach the poles).
#     For more information, see: https://en.wikipedia.org/wiki/Decimal_degrees#Precision

import sys
import urllib
import xmltodict
from proj import latLonToWebMercator, webMercatorToLatLon, math

# Save an image of the given lat/lon point for a given tile system information and return the lat/lon coordinates of the top left and bottom right corner of the image.
# If the image could not be recovered, return false.
def saveTileImage(lat, lon, tileInfo, dataType, path="res/tile/"):
    x,y = latLonToWebMercator(lat,lon,True)

    # Convert Web Mercator coordinates of the given point to tile coordinates in the API's tile system
    tileRow = yToTileRow(y,tileInfo)
    tileCol = xToTileCol(x,tileInfo)

    # Convert tile coordinates of the corners in the API's tile system to Web Mercator coordinates
    tileTopLeftX = tileColToX(int(tileCol),tileInfo)
    tileTopLeftY = tileRowToY(int(tileRow),tileInfo)
    tileBottomLeftX = tileColToX(int(tileCol)+1,tileInfo)
    tileBottomLeftY = tileRowToY(int(tileRow)+1,tileInfo)

    # Convert and round Web Mercator coordinates of the corners to lat/lon coordinates
    topLeftLat,topLeftLon = webMercatorToLatLon(tileTopLeftX, tileTopLeftY,True)
    topLeftLat = round(topLeftLat, 6)
    topLeftLon = round(topLeftLon, 6)
    bottomRightLat,bottomRightLon = webMercatorToLatLon(tileBottomLeftX, tileBottomLeftY,True)
    bottomRightLat = round(bottomRightLat, 6)
    bottomRightLon = round(bottomRightLon, 6)

    # Format file name
    zoomLevel = str(tileInfo['zoomLevel'])
    fileName = str(topLeftLat) + '_' + str(topLeftLon) + '_' + str(bottomRightLat) + '_' + str(bottomRightLon) + '_' + dataType + '_' + zoomLevel + '.jpeg'
    
    # Call to API
    try:
        if dataType == 'satellite':
            urllib.request.urlretrieve("https://wxs.ign.fr/essentiels/geoportail/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=ORTHOIMAGERY.ORTHOPHOTOS&TILEMATRIXSET=PM&TILEMATRIX="+zoomLevel+"&TILECOL="+str(tileCol)+"&TILEROW="+str(tileRow)+"&STYLE=normal&FORMAT=image/jpeg", path + fileName)
        if dataType == 'ign':
            urllib.request.urlretrieve("https://wxs.ign.fr/essentiels/geoportail/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2&TILEMATRIXSET=PM&TILEMATRIX="+zoomLevel+"&TILECOL="+str(tileCol)+"&TILEROW="+str(tileRow)+"&STYLE=normal&FORMAT=image/png", path + fileName)
    except urllib.error.HTTPError:
        return False

    return [topLeftLat,topLeftLon], [bottomRightLat,bottomRightLon]

# Retrieve API's tile system information for a given projection identifier
def getTileMatrixInformation(projectionIdentifier):
    tileMatrixInformation = {'projId': projectionIdentifier, 'tiles': []}

    url = "https://wxs.ign.fr/essentiels/geoportail/wmts?SERVICE=WMTS&REQUEST=GetCapabilities"
    data = xmltodict.parse(urllib.request.urlopen(url).read())

    # Retrieve data corresponding to the projection identifier
    for tileMatrixSet in data['Capabilities']['Contents']['TileMatrixSet']:
        if (tileMatrixSet['ows:Identifier'] == projectionIdentifier):
            tileMatrix = tileMatrixSet['TileMatrix']

    # Save relevant data for our application
    for tile in tileMatrix:
        tileInfo = {}
        tileInfo['zoomLevel'] = int(tile['ows:Identifier'])
        tileInfo['resolution'] = float(tile['ScaleDenominator']) / 3571.42857189 # Constant calculated from the Web Mercator scale table given in the API's documentation
        topLeftCorner = tile['TopLeftCorner'].split()
        tileInfo['topLeftCornerX'] = float(topLeftCorner[0])
        tileInfo['topLeftCornerY'] = float(topLeftCorner[1])
        tileInfo['tileWidth'] = int(tile['TileWidth'])
        tileInfo['tileHeight'] = int(tile['TileHeight'])
        tileMatrixInformation['tiles'].append(tileInfo)

    return tileMatrixInformation

# Convert Web Mercator x coordinate to API's tile system column index
def xToTileCol(x,tileInfo):
    return (x - tileInfo['topLeftCornerX']) / (tileInfo['tileWidth'] * tileInfo['resolution'])

# Convert Web Mercator y coordinate to API's tile system row index
def yToTileRow(y,tileInfo):
    return (tileInfo['topLeftCornerY'] - y) / (tileInfo['tileHeight'] * tileInfo['resolution'])

# Convert API's tile system column index to Web Mercator x coordinate
def tileColToX(tileCol,tileInfo):
    return tileCol * tileInfo['tileWidth'] * tileInfo['resolution'] + tileInfo['topLeftCornerX']

# Convert API's tile system row index to Web Mercator y coordinate
def tileRowToY(tileRow,tileInfo):
    return -(tileRow * tileInfo['tileHeight'] * tileInfo['resolution'] - tileInfo['topLeftCornerY'])

# For a given tile corner lat/lon coordinates, compute the center coordinates of the 8 * radius adjacent tiles
# Thanks to: https://math.stackexchange.com/a/206661
def getAdjacentTilesCoord(tileTopLeft, tileBottomRight, radius=1):
    adjacentCoord = []
    latEpsilon = abs(tileTopLeft[0] - tileBottomRight[0]) / 2
    lonEpsilon = abs(tileTopLeft[1] - tileBottomRight[1]) / 2
    latCenter = tileTopLeft[0] - latEpsilon
    lonCenter = tileTopLeft[1] + lonEpsilon

    for r in range(1,radius+1):
        # Minus epsilon/4 to ensure that the edges of the ellipse do not touch the edges of the tile
        yEllipseRadius = (tileTopLeft[0] + 2 * r * latEpsilon) - latCenter - latEpsilon / 4
        xEllipseRadius = (tileBottomRight[1] + 2 * r * lonEpsilon) - lonCenter - lonEpsilon / 4

        for k in range(8*r):
            theta = 2 * math.pi / (8*r) * k
            y = latCenter + yEllipseRadius * math.sin(theta)
            x = lonCenter + xEllipseRadius * math.cos(theta)
            adjacentCoord.append([y,x])

    return adjacentCoord

if __name__ == "__main__":
    if len(sys.argv) != 6:
        print('Wrong arguments, usage: latitude longitude zoomLevel dataType block')
        print('\tlat / lon: must be in decimal degrees')
        print('\tzoomLevel: 0-21')
        print('\tdataType: ign or satellite')
        print('\tblock: block size of the adjacent tiles to retrieve, e.g with a value of 2, it will retrieve 16 tiles around the main tile')
        sys.exit(0)

    lat = round(float(sys.argv[1]), 6)
    lon = round(float(sys.argv[2]), 6)
    zoomLevel = int(sys.argv[3])
    dataType = sys.argv[4]
    block = int(sys.argv[5])

    if zoomLevel < 0 or zoomLevel > 21:
        print('Wrong zoomLevel argument, must be between 0 and 21 included')
        sys.exit(0)
    if block < 0:
        print('Wrong block argument, must be >= 0')
        sys.exit(0)

    tileMatrixInformation = getTileMatrixInformation("PM")
    tile = tileMatrixInformation['tiles'][zoomLevel]
    cornerCoordinates = saveTileImage(lat, lon, tile, dataType)
    if cornerCoordinates:
        print('zoom:', tile['zoomLevel'],'topLeft:', cornerCoordinates[0], 'bottomRight', cornerCoordinates[1])
        if block > 0:
            successCount = 0
            errorCount = 0
            total = (block * 2 + 1)**2 - 1
            for adjacentTile in getAdjacentTilesCoord(cornerCoordinates[0], cornerCoordinates[1], block):
                if saveTileImage(adjacentTile[0], adjacentTile[1], tile, dataType):
                    successCount += 1
                else:
                    errorCount += 1
                    print("Could not retrieve adjacent tile", dataType, "at zoom level", tile['zoomLevel'])
                print(str(successCount)+'/'+str(total)+' ('+str(errorCount)+' error(s))')
    else:
        print("Could not retrieve", dataType, "at zoom level", tile['zoomLevel'], "ending..")