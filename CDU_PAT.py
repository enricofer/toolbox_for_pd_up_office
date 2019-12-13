
# Import system modules
import arcpy
import os
import uuid
import tempfile
import json

def clean_fc(name):
    return name.lower().replace("sit.","").replace("_rw","").replace("_r","")
    
def extract_related(selector,all_list):
    lyrs = []
    for item in all_list:
        if item["layer"].lower() == selector:
            item["clean_layer"] = item["layer"].lower()
            lyrs.append(item)
    return lyrs

arcpy.AddMessage("default.gdb_path: %s" % arcpy.env.scratchWorkspace)

default_workspace = arcpy.env.scratchWorkspace
arcpy.AddMessage(arcpy.GetParameterAsText(0))
probe_path = arcpy.GetParameterAsText(0).split('\\')
arcpy.AddMessage("probe_path: %s" % probe_path)

with open(os.path.join(os.path.dirname(__file__),"sit_decodifica_pat.json"), 'r') as f:
    decodifica = json.load(f)
    
cleaned_decodifica = [clean_fc(item["layer"]) for item in decodifica]

arcpy.AddMessage("cleaned_decodifica: %s" % str(cleaned_decodifica))

base_pat_repository = r"Connessioni database\VISIO_R_GDBT.sde\SIT.PAT_r"
arcpy.env.workspace = base_pat_repository
check_layer_list = arcpy.ListFeatureClasses("*")

area_totale = 0
area_zonizzata = 0

with arcpy.da.SearchCursor(os.path.join(arcpy.GetParameterAsText(0)), ["SHAPE","SHAPE@area"]) as cursor:  
    for row in cursor:  
        area_totale += row[1]
arcpy.AddMessage("area totale: %d" % area_totale)

# Set the workspace (to avoid having to type in the full path to the data every time)
#arcpy.env.workspace = r"Connessioni database\VISIO_R_GDBT.sde\SIT.PI"
# Process: Find all stream crossings (points)
    
output = []

for check_layer in check_layer_list:
    arcpy.AddMessage("check_layer: %s, %s, %s" % (check_layer,clean_fc(check_layer),str(clean_fc(check_layer) in cleaned_decodifica)))
    desc = arcpy.Describe(check_layer)
    
    if clean_fc(check_layer) in cleaned_decodifica:
        related_list = extract_related(clean_fc(check_layer),decodifica)
        for related in related_list:
            arcpy.AddMessage("cleaned_check_layer: %s, campo: %s, valore: %s" % (clean_fc(check_layer),related["campo"],related["valore"]))
            arcpy.AddMessage("check_layer type: %s" % desc.shapeType)
            if desc.shapeType == 'Polygon':
                intersect_layer = check_layer
            else:
                intersect_layer = os.path.join(default_workspace,"buffer_%s" % uuid.uuid4().hex)
                arcpy.Buffer_analysis(check_layer, intersect_layer, "0.1")
            
            
            target_lyr = arcpy.mapping.Layer(intersect_layer)
            if related["campo"]:
                target_lyr.definitionQuery = "%s = '%s'" % (related["campo"], related["valore"])
            
            inFeatures = [probe_path, target_lyr]
            intersectOutput = os.path.join(default_workspace,"IntersectOutputResult_%s" % uuid.uuid4().hex)
            clusterTolerance = 0    
            arcpy.Intersect_analysis(inFeatures, intersectOutput, "", clusterTolerance, "input")
            
            result = arcpy.GetCount_management(intersectOutput)
            intersected_feats = int(result.getOutput(0))
            arcpy.AddMessage("check_layer intesected feats: %d" % intersected_feats)
            if intersected_feats > 0:
                output.append ({
                    "layer": clean_fc(check_layer),
                    "fc": check_layer,
                    "desc": related["descrizione"],
                    "nta": related["nta"]
                })

arcpy.AddMessage(json.dumps(output,indent=3))

arcpy.SetParameterAsText(2,json.dumps(output,indent=3))

arcpy.AddMessage(arcpy.GetParameterAsText(1))
if arcpy.GetParameterAsText(1):
    with open(arcpy.GetParameterAsText(1),"w") as f:
        f.write(json.dumps(output, indent=3))