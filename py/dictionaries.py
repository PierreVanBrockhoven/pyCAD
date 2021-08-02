DEFAULT = {
"wallType":107,
"roofType":207,
"floorType":307,
"openableRatio":0.5,
"glazingRatio":0.2,
"Ninf":0.3,
"glazingGValue":0.49,
"glazingUValue":1.7,
"psi":0.2
}
# year : WallType, RoofType, FloorType, Ninf, glazing_Uvalue, glazing_Gvalue
THRESHOLDS = {
    1945: (100, 200, 300, 0.7, 2.3, 0.47),
    1960: (101, 201, 301, 0.6, 2.3, 0.47),
    1970: (102, 202, 302, 0.55, 2.3, 0.47),
    1980: (103, 203, 303, 0.5, 2.3, 0.47),
    1990: (104, 204, 304, 0.4, 2.3, 0.47),
    2000: (105, 205, 305, 0.35, 2.3, 0.47),
    2021: (106, 206, 306, 0.3, 1.7, 0.49),
}

# gbaup : year threshold
PERIODS = {
    "8010": 1945,
    "8011": 1945,
    "8012": 1945,
    "8013": 1960,
    "8014": 1970,
    "8015": 1980,
    "8016": 1985,
    "8017": 1990,
    "8018": 1995,
    "8019": 2000,
    "8020": 2005,
    "8021": 2010,
    "8022": 2015,
    "8023": 2020,
}
# buildings names linked with EGID
BUILDINGS = {
    "919275": {
        "Name": "Tour du Stade",
        "OccupancyYearProfile": 1,
        "footprint": 3027.25,
        "surfByPers": 20, #15
        "n": 0,
        "Tmin":20,
        "Tmax":24,
    },
    "919276": {
        "Name": "Ariana",
        "OccupancyYearProfile": 1,
        "footprint": 3027.25,
        "surfByPers": 20, #15
        "n": 0,
        "Tmin":20,
        "Tmax":24,
    },
    "919279": {
        "Name": "Plein-Ciel A",
        "OccupancyYearProfile": 1,
        "footprint": 3027.25,
        "surfByPers": 20, #15
        "n": 0,
        "Tmin":20,
        "Tmax":24,
    },
}
# merging id : merged building new name (= sub station name), building to merge 1, building to merge 2, ...
MERGING = {
    0: ("All", "Tour du Stade", "Ariana","Plein-Ciel A"),

}
# max face orientation : window ratio
# 0° = North
# 90° = West
GLAZING_RATIO = {
    45: "0.15",
    90: "0.2",
    135: "0.25",
    180: "0.3",
    225: "0.3",
    270: "0.25",
    315: "0.2",
    360: "0.15",
}

SUB_STATIONS = {

    "All": {
        "substationId": 100,
        "designThermalPower": 330000,  # P condenseur
        "designTempDifference": 5,
        "Pmax": 263,  # kW
        "HPRatio": 1,  # P_HP/P_tot
    },
}
