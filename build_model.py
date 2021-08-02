import sys
sys.path.append( "py/")
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import requests
import math
import csv
from collections import OrderedDict
from os.path import abspath, dirname, join, exists, os
from time import time
from datetime import datetime
from termcolor import colored
from py import dictionaries as dict
from py import fun

GEOADMIN_BASE_URL = "https://api.geo.admin.ch/rest/services/ech/MapServer/ch.bfs.gebaeude_wohnungs_register/"
CURRENT_FILE_DIR = dirname(abspath(__file__))

def timeit(fun):
    """
    Decorator who times the functions.
    """
    def timed(*args, **kw):
        start = time()
        result = fun(*args, **kw)
        end = time()
        elapsed_time = round(end - start, 3)
        print(colored("Execution time : {} sec".format(elapsed_time),'cyan'))
        return result

    return timed

def set_model(input_xml: str, output_xml: str,geometry_writer):
    """
    Retrieves the RegBL data of the building from the Swisstopo API using its EGID number.
    Then, defines the physical parameters of the buildings (WallType, Ninf, ...) based on
    the type of building and year or period of construction.

    Note :
    The Building key attribute in the CitySim model must absolutely be
    the EGID number of the building (if it is an existing building).
    """
    tree = ET.parse(input_xml)
    root = tree.getroot()

    for building in root.iter("Building"):

        EGID = building.attrib["key"]

        building.set("Name",dict.BUILDINGS[EGID]["Name"])
        # new building
        if EGID.isdigit() is False:
            Ninf = str(dict.DEFAULT['Ninf'])
            wallType = str(dict.DEFAULT['wallType'])
            roofType = str(dict.DEFAULT['roofType'])
            floorType = str(dict.DEFAULT['floorType'])
            glazing_Gvalue = str(dict.DEFAULT['glazingGValue'])
            glazing_Uvalue = str(dict.DEFAULT['glazingUValue'])


        # old building
        else:
            # scrapping
            url = GEOADMIN_BASE_URL + str(EGID) + "_0"
            response = requests.get(url=url)

            # scrapping blocked by GEOADMIN
            if response.status_code != 200:
                print("Scrapping blocked by GeoAdmin")

            else:
                regbl = response.json()

                #building.set("Name",regbl["feature"]["attributes"]["gbez"])
                # retrieving data
                try:
                    construction_period = int(regbl["feature"]["attributes"]["gbaup"])
                    construction_period = dict.PERIODS[str(construction_period)]

                except KeyError as err:
                    print(colored("The [gbauj] key has not been reached for building {} : {}".format(EGID,dict.BUILDINGS[EGID]),'red'))

            for year in dict.THRESHOLDS.keys():
                if construction_period <= year:
                    wallType, roofType, floorType, Ninf, glazing_Uvalue, glazing_Gvalue = dict.THRESHOLDS[year]
                    break

        # setting wall type & glazing ratio
        for wall in building.iter("Wall"):
            wall.set("type", str(wallType))
            wall.set("GlazingGValue", str(glazing_Gvalue))
            wall.set("GlazingUValue", str(glazing_Uvalue))
            wall.set("OpenableRatio",str(dict.DEFAULT['openableRatio']))
            if geometry_writer != False:
                for v in wall:
                    geometry_writer.writerow([building.attrib['key'],wall.attrib['id'],'wall',v.attrib['x'],v.attrib['y'],v.attrib['z']])

             # setting glazing ratio
            wall.set("GlazingRatio",fun.get_glazing_ratio(wall))

        surface_tot = 0
        for roof in building.iter("Roof"):
            X = []
            Y = []
            for v in roof:
                if v.tag != "ST":
                    X.append(float(v.attrib['x']))
                    Y.append(float(v.attrib['y']))
                    n = len(X)
                    surf = fun.polygonArea(X, Y, n)
            surface_tot = surface_tot + surf
        #print("{} : {} m²".format(building.attrib["Name"],surface_tot))
        # setting roof type
        for roof in building.iter("Roof"):
            roof.set("type",str(roofType))
            if geometry_writer != False:
                for v in roof:
                    geometry_writer.writerow([building.attrib['key'],roof.attrib['id'],'roof',v.attrib['x'],v.attrib['y'],v.attrib['z']])


        # setting floor type
        for floor in building.iter("Floor"):
            floor.set("type",str(floorType))
            if geometry_writer != False:
                for v in floor:
                    geometry_writer.writerow([building.attrib['key'],floor.attrib['id'],'floor',v.attrib['x'],v.attrib['y'],v.attrib['z']])


        for zone in building.iter("Zone"):
            zone.set("psi",str(dict.DEFAULT['psi']))
            zone.set("Tmin",str(dict.BUILDINGS[EGID]["Tmin"]))
            zone.set("Tmax",str(dict.BUILDINGS[EGID]["Tmax"]))
            vol = float(zone.attrib["volume"])

            if (dict.BUILDINGS[EGID]["n"] == 0):
                n = (1/dict.BUILDINGS[EGID]["surfByPers"])*0.8*vol/(2.7)

            else:
                n = dict.BUILDINGS[EGID]["n"]

            for occupants in zone.iter("Occupants"):
                occupants.set("type",str(dict.BUILDINGS[EGID]["OccupancyYearProfile"]))
                occupants.set("n",str(int(n)))
                #occupants.set("type","1")
                occupants.set("DHWType","1")


        # setting building air infiltration rate
        building.set("Ninf", str(Ninf))
    print("[{}] Merging buildings - ".format(datetime.now().strftime('%H:%M:%S')),end='')

    for i in dict.MERGING.keys():

        j = 1
        to_merge = []

        # getting buildings to merge in xml
        while j < len(dict.MERGING[i]):
            to_merge.append(root.find(".//*[@Name='"+dict.MERGING[i][j]+"']"))
            j+=1

        vol = 0
        Ninf = 0
        k = 0


        # iterating over each substation's building to merge
        for building in to_merge:

            # calculating mean Ninf
            Ninf = Ninf + float(building.attrib["Ninf"])
            k+=1

            for zone in building.iter("Zone"):
                # calculating volume sum
                vol = vol + float(zone.attrib["volume"])

                # assigning building id to its zone
                zone.attrib["id"] = building.attrib["key"]

            # copying <Zone> xml element to substation
            # Trick to avoid duplicating zone of first merged building : comparing
            # current zone volume with merged volume
            if (round(float(vol))) != round(float(building.attrib["Vi"])):
                to_merge[0].append(zone)

            # removing merged buildings from xml
            if k > 1:
                for buildings in root.iter("District"):
                    buildings.remove(building)

        # setting substation attributes
        to_merge[0].set("Name",dict.MERGING[i][0])
        to_merge[0].set("key",dict.MERGING[i][0])
        to_merge[0].set("Vi",str(vol))
        to_merge[0].set("Ninf",str(Ninf/k))


    print(colored("Done",'green'))
    print("[{}] Setting CAD substations - ".format(datetime.now().strftime('%H:%M:%S')),end='')
    for building in root.iter("Building"):
        # checking if current building is a CAD sub-station
        if (building.attrib["Name"] in dict.SUB_STATIONS):
            # if so, changing heatsource from boiler to sub-station
            for boiler in building.iter("Boiler"):
                # removing irrelevant attributes
                boiler.attrib.pop("name")
                boiler.attrib.pop("Pmax")
                boiler.attrib.pop("eta_th")
                # upadting xml tag name fom "<Boiler/>" to  "<Substation/>"
                boiler.tag="Substation"
                substation = boiler
                # setting sub-station attibutes
                substation.set('type','simple')
                substation.set('designEpsilon','0.8')
                substation.set('linkedNodeId',str(dict.SUB_STATIONS[building.attrib["Name"]]["substationId"]))
                substation.set('designThermalPower',str(dict.SUB_STATIONS[building.attrib["Name"]]["designThermalPower"]))
                substation.set('designTempDifference',str(dict.SUB_STATIONS[building.attrib["Name"]]["designTempDifference"]))

            for roof in building.iter("Roof"):
                # adding thermal solar panels only for ilots
                if "ILOT" in building.attrib['Name']:
                    ST = ET.SubElement(roof,'ST')
                    ST.set('stRatio',str(dict.ST_SPEC['stRatio']))
                    ST.set('name',dict.ST_SPEC['name'])
                    ST.set('eta0',dict.ST_SPEC['eta0'])
                    ST.set('a1',dict.ST_SPEC['a1'])
                    ST.set('a2',dict.ST_SPEC['a2'])

    print(colored("Done",'green'))



    tree.write(output_xml,encoding="ISO-8859-1",xml_declaration=True)

    # removing temp_xml
    os.remove(input_xml)

def preprocessing(raw_xml:str,composites_xml: str,occupancy_xml:str,DHW_xml:str,CAD_xml:str,output_xml:str):
    """
    Pre-processing raw model before parsing : including composites XML
    and District Energy Center (CAD) XML into the model, followwing a
    find & replace approach.
    A temporary model (temp_model.xml) is generated, used afterwards
    for parsing in the set_model() function. When the final model is
    set, temp_model.xml is deleted.
    """
    print("[{}] Pre-processing - ".format(datetime.now().strftime('%H:%M:%S')),end='')

    #check if a temp_xml.xml file has already been created
    if os.path.exists('outputs/temp_model.xml'):
        os.remove('outputs/temp_model.xml')
    # remove irelevant processed model generated from previous run if exists
    if os.path.exists(output_xml):
        os.remove(output_xml)


    raw_model = open(raw_xml).read()

    find = ["<!-- Composites -->","<!-- Occupancy -->", "<!-- DHW -->","<!-- CAD -->"]
    replace = [open(composites_xml).read(),open(occupancy_xml).read(),open(DHW_xml).read(),open(CAD_xml).read()]

    for i in range(len(find)):
        raw_model = raw_model.replace(find[i],replace[i])

    output_file = open('outputs/temp_model.xml',"w")
    output_file.write(raw_model)
    output_file.close()

    print(colored("Done",'green'))

@timeit
def main():

    raw_xml = join(CURRENT_FILE_DIR, "inputs/model_in.xml")
    temp_xml = join(CURRENT_FILE_DIR, "outputs/temp_model.xml")
    composites_xml = join(CURRENT_FILE_DIR, "inputs/composites.xml")
    occupancy_xml = join(CURRENT_FILE_DIR, "inputs/occupancy.xml")
    CAD_xml = join(CURRENT_FILE_DIR, "inputs/CAD.xml")
    DHW_xml = join(CURRENT_FILE_DIR, "inputs/DHW.xml")

    # file used to write buildings geometries for future import in database
    if os.path.exists('outputs/geometry.csv'):
        os.remove('outputs/geometry.csv')
    geometry = open("outputs/geometry.csv","w")

    geometry_writer = csv.writer(geometry, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    geometry_writer.writerow(['EGID','id','type','x','y','z'])

    print(colored("Building model",'magenta'))

    output_xml = join(CURRENT_FILE_DIR, "outputs/model_out.xml")

    preprocessing(raw_xml=raw_xml,composites_xml=composites_xml,occupancy_xml=occupancy_xml,DHW_xml=DHW_xml,CAD_xml=CAD_xml,output_xml=output_xml)
    set_model(input_xml=temp_xml, output_xml=output_xml,geometry_writer=geometry_writer)

    geometry_writer = False
    geometry.close()

    print(colored("MODEL BUILT !",'green'))

if __name__ == "__main__":
    main()
