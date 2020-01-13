
# Import system modules
import arcpy
import os
import uuid
import tempfile
import json

current_workspace = arcpy.env.scratchWorkspace

arcpy.AddMessage(arcpy.GetParameterAsText(0))
probe_path = arcpy.GetParameterAsText(0)#.split('\\')
tolleranza = float(arcpy.GetParameterAsText(1))
arcpy.AddMessage("probe_path: %s" % probe_path)

with open(os.path.join(os.path.dirname(__file__),"sit_decodifica_con_descrizioni.json"), 'r') as f:
    decodifica = json.load(f)

check_layer_list = [
    r"Connessioni database\VISIO_R_GDBT.sde\FERREGUTIE.CS_unitaDiPiano",
]

area_totale = 0

with arcpy.da.SearchCursor(os.path.join(arcpy.GetParameterAsText(0)), ["SHAPE","SHAPE@area"]) as cursor:  
    for row in cursor:  
        area_totale += row[1]
arcpy.AddMessage("area totale: %d" % area_totale)

output = []

for check_layer in check_layer_list:
    arcpy.AddMessage("check_layer: %s" % check_layer)
    inFeatures = [probe_path, check_layer]
    intersectOutput = os.path.join(current_workspace,"IntersectOutputResult_%s" % uuid.uuid4().hex)
    clusterTolerance = 0    
    arcpy.Intersect_analysis(inFeatures, intersectOutput, "", clusterTolerance, "input")
    
    with arcpy.da.SearchCursor(intersectOutput, ["FULL_ID","DESPRO", "NORMA1", "DESPRO1", "SHAPE@area" ]) as cursor:
        
        for row in cursor:  
            if row[4] > area_totale*tolleranza/100:
                arcpy.AddMessage(str(row))
                row_desc = {
                    "full_id": row[0],
                    "despro": row[1],
                    "norma1": row[2],
                    "despro1": row[3],
                    "area": row[4]
                }
                output.append(row_desc)
                
        del cursor  

arcpy.AddMessage(json.dumps(output,indent=3))

arcpy.SetParameterAsText(3,json.dumps(output))

arcpy.AddMessage(arcpy.GetParameterAsText(2))
if arcpy.GetParameterAsText(2):
    with open(arcpy.GetParameterAsText(2),"w") as f:
        f.write(json.dumps(output, indent=3))