import requests
import json
from types import SimpleNamespace
from proj import degToRad, math

# Returns the distance along the surface of the earth for the given coordinates.
# Uses haversine formula: a = sin²(Δφ/2) + cosφ1·cosφ2 · sin²(Δλ/2); d = 2 · atan2(√a, √(a-1)).
def calculDistance(longNO, latNO, longSE, latSE):
    R = 6371e3 # Earth radius
    lat1 = degToRad(latNO)
    lat2 = degToRad(latSE)
    lon1 = degToRad(longNO)
    lon2 = degToRad(longSE)
    deltaLat = lat2 - lat1
    deltaLong = lon2 - lon1
    a = math.sin(deltaLat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(deltaLong/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = R * c

    return d

def altitude(longNO, latNO, longSE, latSE, resolution, output, gui=None):
    sampling = int(math.sqrt(int(resolution)))
    E = (float(latSE) - float(latNO)) / (sampling-1)

    elevationTab = []

    ### A PARALLELISER
    ### EN SORTIE DE BOUCLE, TOUT DOIT ETRE DANS elevationTab

    for k in range(sampling):
        listLong = "{}|{}".format(longNO, longSE)
        listLat = "{}|{}".format(str(latNO + k*E), str(latNO + k*E))
        
        #print(listLat)

        response_API = requests.get("https://wxs.ign.fr/essentiels/alti/rest/elevationLine.json?sampling={}&lon={}&lat={}&indent=true".format(str(sampling), listLong, listLat))
        data = response_API.text
        x = json.loads(data, object_hook=lambda d: SimpleNamespace(**d))
        #print('REQUETE TERMINEE \n')

        for i in range(0, len(x.elevations)):
            elevationTab.append(x.elevations[i])

        progress = str(k+1)+"/"+str(sampling)
        if gui != None:
            gui.progressBarText.set("Progression : données d'élévation.. "+progress)
            gui.progressBar['value'] += 50/sampling
            gui.update()
        else:
            print(progress)

    ### FIN SECTION A PARALLELISER

    #print(elevationTab)

    # Normalisation des axes x,y (conversion distance lat/lon entre points en mètres) et écriture dans fichier
    nbPointParLigne = int(math.sqrt(int(resolution)))
    latDistance = calculDistance(longNO, latNO, longNO, latSE)
    lonDistance = calculDistance(longNO, latNO, longSE, latNO)
    #print(latDistance, lonDistance)
    latOffset = latDistance / (nbPointParLigne - 1)
    lonOffset = lonDistance / (nbPointParLigne - 1)

    #print(latOffset, lonOffset)

    f = open(output, "w")
    for i in range(nbPointParLigne):
        for j in range(nbPointParLigne):
            index = i * nbPointParLigne + j
            elevationTab[index].lat = round(i * latOffset, 3)
            elevationTab[index].lon = round(j * lonOffset, 3)
            f.write(str(elevationTab[index].lon) + " " + str(elevationTab[index].lat) + " " + str(elevationTab[index].z) + "\n")
    f.close()

"""
latNO, longNO = 45.537137, 6.855469 #49.199654, -0.395508 
latSE, longSE = 45.521744, 6.877441 #49.196064, -0.390015
resolution = input('Nombre de points souhaité : (min = 10) ')
altitude(longNO, latNO, longSE, latSE, resolution, "res/altitude/res.xyz")
"""
