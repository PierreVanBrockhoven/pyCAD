import numpy as np
import math
from collections import OrderedDict
import dictionaries as dict
import xml.etree.ElementTree as ET

def get_glazing_ratio(wall):
    polygon = []
    i = 0
    for point in wall:
        singlePoint = [
        float(point.attrib['x']),
        float(point.attrib['y']),
        float(point.attrib['z'])
        ]
        i+=1
        polygon.append(singlePoint)
        if i == 3:
            break

    normal = vector(polygon)

    # azimut 0° => Vecteur unitaire pointant vers le nord
    north = [0,1,0]

    # check if wall is not an horizontal surface
    if(abs(normal[2]) != 1 ):
        azimut = math.degrees(np.arccos(np.dot(north,normal)))
        for _AZIMUT in dict.GLAZING_RATIO.keys():
            if azimut <= _AZIMUT:
                glazing_ratio = dict.GLAZING_RATIO[_AZIMUT]
                break


        return glazing_ratio
    else:
        return "0"

def vector(polygon_coordinate):
    # getting the vector from cross product

    u = np.float64(np.array(polygon_coordinate[2]) - np.array(polygon_coordinate[1]))
    v = np.float64(np.array(polygon_coordinate[1]) - np.array(polygon_coordinate[0]))


    # normal vector
    if np.linalg.norm(u) == 0:
        n = v
    elif np.linalg.norm(v) == 0:
        n = u
    else:
        n = np.cross(u, v)
    n = n / np.linalg.norm(n)
    return n

def roof_surface(model_xml:str,scenario:int):

    surface_tot = 0
    tree = ET.parse(model_xml)
    root = tree.getroot()

    for building in root.iter("Building"):

        if building.attrib["Name"] in dict.SUB_STATIONS and dict.SUB_STATIONS[building.attrib["Name"]]["ST"] == True and int(dict.SUB_STATIONS[building.attrib["Name"]]["scenario"]) == scenario:
            for roof in building.iter("Roof"):
                X = []
                Y = []
                for v in roof:
                    if v.tag != "ST":
                        X.append(float(v.attrib['x']))
                        Y.append(float(v.attrib['y']))
                        n = len(X)
                        surf = polygonArea(X, Y, n)
                surface_tot = surface_tot + surf
                #print("{} : {} m²".format(building.attrib["Name"],surf))
    return surface_tot

#def floors_numbers(volume:float,)
def get_scenarios():
    scenarios = []
    for i in dict.SUB_STATIONS:
        scenarios.append(int(dict.SUB_STATIONS[i]["scenario"]))

    scenarios = list(OrderedDict.fromkeys(scenarios))
    return scenarios

def polygonArea(X, Y, n):

    # Initialze area
    area = 0.0

    # Calculate value of shoelace formula
    j = n - 1
    for i in range(0,n):
        area += (X[j] + X[i]) * (Y[j] - Y[i])
        j = i   # j is previous vertex to i

    # Return absolute value
    return int(abs(area / 2.0))

def network_length(root):
    length = 0
    # getting network length to estimates network  and civil engineering cost
    for pipes in root.iter("PipePair"):
        length = length + float(pipes.attrib["length"])
    return length
def wkb_hexer(poly):
    return poly.wkb_hex
