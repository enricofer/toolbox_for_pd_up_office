
# Import system modules
import arcpy
import os
import uuid
import tempfile
import json

arcpy.AddMessage("default.gdb_path: %s" % arcpy.env.workspace)

current_workspace = arcpy.env.scratchWorkspace

arcpy.AddMessage(arcpy.GetParameterAsText(0))
probe_path = arcpy.GetParameterAsText(0)
arcpy.AddMessage("probe_path: %s" % probe_path)

if not arcpy.Exists(probe_path):
    arcpy.AddError("Ciao")
    raise arcpy.ExecuteError

with open(os.path.join(os.path.dirname(__file__),"sit_decodifica_con_descrizioni.json"), 'r') as f:
    decodifica = json.load(f)

check_layer_list = [
    r"Connessioni database\VISIO_R_GDBT.sde\SIT.DBTOPOGRAFICO\SIT.UN_VOL",
]

area_totale = 0

with arcpy.da.SearchCursor(arcpy.GetParameterAsText(0), ["SHAPE","SHAPE@area"]) as cursor:  
    for row in cursor:  
        area_totale += row[1]
arcpy.AddMessage("area totale: %d" % area_totale)

# Set the workspace (to avoid having to type in the full path to the data every time)
#arcpy.env.workspace = r"Connessioni database\VISIO_R_GDBT.sde\SIT.PI"
# Process: Find all stream crossings (points)
    
output = [
    {
        "layer": 0, 
        "definizione": "Area totale", 
        "nome": "Area totale", 
        "url": "", 
        "gruppo": "cdu", 
        "area": area_totale, 
        "note": None, 
        "articolo": 0, 
        "interno_pe": 0
    },
]

SC_totale = 0
VOL_totale = 0

probe_list = []
with arcpy.da.SearchCursor(probe_path, 'SHAPE@') as scur:
    for row in scur:
        probe_list.append(row[0])
arcpy.AddMessage("PROBELIST: %s" % str(probe_list))
probe_list_lyr = arcpy.CopyFeatures_management(probe_list, r"in_memory\zo")

for check_layer in check_layer_list:
    arcpy.AddMessage("check_layer: %s" % check_layer)
    desc = arcpy.Describe(check_layer)
    arcpy.AddMessage("check_layer type: %s" % desc.shapeType)
    if desc.shapeType == 'Polygon':
        intersect_layer = check_layer
    else:
        intersect_layer = os.path.join(current_workspace,"buffer_%s" % uuid.uuid4().hex)
        arcpy.Buffer_analysis(check_layer, intersect_layer, "0.1")

    inFeatures = [probe_list_lyr, check_layer]
    intersectOutput = os.path.join(current_workspace,"IntersectOutputResult_%s" % uuid.uuid4().hex)
    clusterTolerance = 0    
    arcpy.Intersect_analysis(inFeatures, intersectOutput, "", clusterTolerance, "input")
    
    with arcpy.da.SearchCursor(intersectOutput, ["UN_VOL_AV", "SHAPE@area" ]) as cursor:  
        arcpy.AddMessage("cursor: %s" % cursor)
        for row in cursor:  
            VOL_totale += row[0] * row[1]
            SC_totale += row[1]
            
    del cursor  

arcpy.Delete_management(probe_list_lyr)

output = {
    "area_totale": area_totale,
    "sc_totale": SC_totale,
    "vol_totale": VOL_totale,
    "copertura": SC_totale * 199 / area_totale,
    "indice": VOL_totale / area_totale
}

arcpy.AddMessage(json.dumps(output,indent=3))

arcpy.SetParameterAsText(1,json.dumps(output))
