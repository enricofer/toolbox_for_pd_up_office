
# Import system modules
import arcpy
import os
import uuid
import tempfile
import json

arcpy.AddMessage("default.gdb_path: %s" % arcpy.env.workspace)

current_workspace = arcpy.env.scratchWorkspace

arcpy.AddMessage(arcpy.GetParameterAsText(0))
probe_path = arcpy.GetParameterAsText(0).split('\\')
arcpy.AddMessage("probe_path: %s" % probe_path)

with open(os.path.join(os.path.dirname(__file__),"sit_decodifica_con_descrizioni.json"), 'r') as f:
    decodifica = json.load(f)

check_layer_list = [
    r"Connessioni database\VISIO_R_GDBT.sde\SIT.PI\SIT.PI_zoning",
    r"Connessioni database\VISIO_R_GDBT.sde\SIT.PI\SIT.PI_perimetri",
    r"Connessioni database\VISIO_R_GDBT.sde\SIT.PI\SIT.PI_linee",
]

area_totale = 0
area_zonizzata = 0

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
    
    with arcpy.da.SearchCursor(intersectOutput, ["LAYER", "NOTE", "INTERNO_PER", "SHAPE@area" ]) as cursor:  
        arcpy.AddMessage("cursor: %s" % cursor)
        for row in cursor:  
            arcpy.AddMessage(str(row))
            layer_id = row[0]
            row_desc = dict(decodifica[str(layer_id)])
            row_desc["layer"] = layer_id
            row_desc["note"] = row[1]
            row_desc["interno_pe"] = row[2]
            row_desc["area"] = row[3]
            output.append(row_desc)
            #arcpy.AddMessage("%s %s %s" % (check_layer,check_layer_list[0], str(check_layer == check_layer_list[0])))
            if check_layer == check_layer_list[0]:
                area_zonizzata += row[3]
            
    del cursor  

if int(area_totale) != int(area_zonizzata):
    output.append(    {
            "layer": 999, 
            "definizione": "Area non zonizzata (viabilità, fiumi, etc)", 
            "nome": "Area non zonizzata", 
            "url": "", 
            "gruppo": "cdu", 
            "area": area_totale-area_zonizzata, 
            "note": None, 
            "articolo": 0, 
            "interno_pe": 0
        }
    )

arcpy.AddMessage(json.dumps(output,indent=3))

arcpy.SetParameterAsText(2,json.dumps(output,indent=3))

arcpy.AddMessage(arcpy.GetParameterAsText(1))
if arcpy.GetParameterAsText(1):
    with open(arcpy.GetParameterAsText(1),"w") as f:
        f.write(json.dumps(output, indent=3))