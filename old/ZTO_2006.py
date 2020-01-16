
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
    r"Connessioni database\VISIO_R_GDBT.sde\SIT.ZONOM\SIT.FCL_ZONEOM",
]

area_totale = 0

with arcpy.da.SearchCursor(arcpy.GetParameterAsText(0), ["SHAPE","SHAPE@area"]) as cursor:  
    for row in cursor:  
        area_totale += row[1]
arcpy.AddMessage("area totale: %d" % area_totale)

zone = {}

for check_layer in check_layer_list:
    arcpy.AddMessage("check_layer: %s" % check_layer)
    desc = arcpy.Describe(check_layer)
    arcpy.AddMessage("check_layer type: %s" % desc.shapeType)
    if desc.shapeType == 'Polygon':
        intersect_layer = check_layer
    else:
        intersect_layer = os.path.join(current_workspace,"buffer_%s" % uuid.uuid4().hex)
        arcpy.Buffer_analysis(check_layer, intersect_layer, "0.1")

    inFeatures = [probe_path, check_layer]
    intersectOutput = os.path.join(current_workspace,"IntersectOutputResult_%s" % uuid.uuid4().hex)
    clusterTolerance = 0    
    arcpy.Intersect_analysis(inFeatures, intersectOutput, "", clusterTolerance, "input")
    
    with arcpy.da.SearchCursor(intersectOutput, ["TIPO_OMO", "SHAPE@area" ]) as cursor:  
        arcpy.AddMessage("cursor: %s" % cursor)
        for row in cursor:  
            zona = row[0]
            if zona in zone:
                zone[zona] += row[1]
            else:
                zone[zona] = row[1]
            
    del cursor  

arcpy.AddMessage(json.dumps(zone,indent=3))

arcpy.SetParameterAsText(1,json.dumps(zone))
