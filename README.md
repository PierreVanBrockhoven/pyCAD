# pyCAD

*Created by Pierre Van Brockhoven, with the precious help & support of Cédric Serugendo* 👌

This script allows to automatically create a CitySim model by specifying the physical properties of the studied buildings, the occupancy and domestic hot water (DHW) profiles.
Moreover, it is also possible to add a district heating network to the model by specifying its characteristics.

## Project structure
```bash
│   build_model.py
│   README.md
│
├───inputs
│   │   CAD.xml
│   │   composites.xml
│   │   model_in.xml
│   │   DHW.xml
│   │   occupancy.xml
│
├───outputs
│       geometry.csv
│       model_out.xml
│
├───py
│   │   dictionaries.py
│   │   fun.py
│
├───skp
│       model.dxf
│       model.skb
│       model.skp
│
```


### Input files required (*inputs* directory)

#### `CAD.xml`
Describe the district energy center items with their physical parameters : thermal station, pipes pair, energy conversion devices, nodes pairs, ...

This file is where you set the network topology.

⚠️ Substations have to be defined in `py/dictionaries.py` file.

#### `composites.xml`
Provide physical data about walls, roofs, floors and grounds as the `<Composite>` xml tag shown below 👇

```XML
<Composite Uvalue="0.94" id="100" name="Neuchatel 1900-1945 adapted" category="Wall">
    <Layer Conductivity="0.08" Cp="1000.0" Density="300.0" Name="Insulating Rendering" Thickness="0.02" />
    <Layer Conductivity="0.81" Cp="1045.0" Density="1600.0" Name="Rubble Masonry" Thickness="0.4" />
    <Layer Conductivity="0.021" Cp="800.0" Density="900.0" Name="Insulating plaster" Thickness="0.02" />
</Composite>
```

#### `dictionaries.py`

This file contains a set of dictionaries used when creating the model. These dictionaries give data about substations (thermal power, design temperature difference, ...), buildings names linked with EGID, time thresholds, buildings to be merged to fit the CAD network, ...

For example, a substation to which all buildings are connected will be described this way:
```python
SUB_STATIONS = {

    "All": {
        "substationId": 100,
        "designThermalPower": 330000,  # P condensor (W)
        "designTempDifference": 5,
        "Pmax": 263,  # kW
        "HPRatio": 1,  # P_HP/P_tot
    },
}
```

#### `model_in.xml`

The xml given by CitySim when saving after importing from DXF. The Sketchup model is located in the *skp* directory.

⚠️ 4 comments has to be added in the raw model to perform preprocessing:
1. `<!-- Composites -->` in place of default composites 👇
```XML
</FarFieldObstructions>
<!-- Composites -->
```
2. `<!-- CAD -->`, `<!-- DHW -->` and `<!-- Occupancy -->` right before the first `<Building>` xml tag. These tags will be replaced by the contents of the inputs files.


### Output files (*outputs* directory)

After running *build_model.py*, the final model (`outputs/model_out.xml`) ready to be used in CitySim and `outputs/geometry.csv` files are created.
The `geometry.csv` file is written during the parsing process (see below). It contains the x, y, z coordinates of each point of each building in addition to EGID number, entity type (wall, roof or floor) and entity id.

Sample :
```csv
EGID,id,type,x,y,z
280000436,12862,wall,1980.10,2889.30,11.52
280000436,12862,wall,1980.10,2889.30,4.14
280000436,12862,wall,1977.62,2878.00,4.14
```
This file can be used to insert buildings geometries into a database for example.
### Creating the model
When these files are in place, you can run `build_model.py` and let the magic happens ✨.
Here is a summary of the operations which are taking place.

#### 1. Preprocessing
First the composites, the CAD network, the domestic hot water profiles and the occupancy profiles are included into the raw model. This is the point of the mandatory comments `<!-- Composites -->`, `<!-- CAD -->`, `<!-- DHW -->` and `<!-- Occupancy -->`. These "find and replace" actions are performed during preprocessing.  
#### 2. Scraping
When preprocessing is done, physical properties of each buildings are set. Scraping requests are made on the [Swiss Geoportail](https://map.geo.admin.ch) to retrieve the construction year or the construction period, and edit physical parameters accordingly.




#### 3. Merging buildings  
Each substation can be linked to only one building. However, it is a common situation to have a substation providing energy to several buildings in reality. So we have to merge them in a single building.

Basically, the `<Zone>` tag of buildings to be merged are gathered in a single `<Building>` tag. This resulting building contains the geometry of each merged building, and its volume and air infiltration rate (Ninf) are updated accordingly. The resulting volume is the sum of each merged building volume, while Ninf is the mean.

Attributes `key` and `Name` are also updated.

Merging rules are described in the `dictionary.py` file :
```python
# merging id : merged building new name (= sub station name), building to merge 1, building to merge 2, ...
MERGING = {
    0: ("All", "Tour du Stade", "Ariana","Plein-Ciel A"),

}
```

#### 4. Setting CAD substations
The final step is to add a substation in merged buildings that need it :
```XML
<HeatSource beginDay="258" endDay="135">
  <Substation type="simple" designEpsilon="0.8" linkedNodeId="40" designThermalPower="200000" designTempDifference="10" />
</HeatSource>
```
