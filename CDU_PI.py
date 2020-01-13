
# Import system modules
import arcpy
import os
import uuid
import tempfile
import json

from sets import Set

arcpy.AddMessage("default.gdb_path: %s" % arcpy.env.workspace)

current_workspace = arcpy.env.scratchWorkspace

arcpy.AddMessage(arcpy.GetParameterAsText(0))
probe_path = arcpy.GetParameterAsText(0)#.split('\\')
arcpy.AddMessage("probe_path: %s" % probe_path)

if not arcpy.Exists(probe_path):
    arcpy.AddError("Ciao")
    raise arcpy.ExecuteError

with open(os.path.join(os.path.dirname(__file__),"sit_decodifica_con_descrizioni.json"), 'r') as f:
    decodifica = json.load(f)

check_layer_list = [
    r"Connessioni database\VISIO_R_GDBT.sde\SIT.PI\SIT.PI_zoning",
    r"Connessioni database\VISIO_R_GDBT.sde\SIT.PI\SIT.PI_perimetri",
    r"Connessioni database\VISIO_R_GDBT.sde\SIT.PI\SIT.PI_linee",
    r"Connessioni database\VISIO_R_GDBT.sde\SIT.PI\SIT.PI_limiti",
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
        "interno_pe": 0,
        "z_omogenea": None
    },
]
zone_scan = {}
layers_scan = []
zone_check = Set()

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

    #zone check
    with arcpy.da.SearchCursor(intersectOutput, ["LAYER", "NOTE", "INTERNO_PER", "SHAPE@area", "OBJECTID"]) as cursor:  
        for row in cursor: 
            if decodifica[str(row[0])]["z_omogenea"]:
                zone_check.add(row[0])
    arcpy.AddMessage("zone_check: %s" % str(zone_check))
    if len(zone_check) > 1:
        parte = True
    else:
        parte = False
    
    with arcpy.da.SearchCursor(intersectOutput, ["LAYER", "NOTE", "INTERNO_PER", "SHAPE@area", "OBJECTID"]) as cursor:  
        arcpy.AddMessage("cursor: %s" % cursor)
        for row in cursor: 
            
            if row[0] == 41 or row[0] in layers_scan: # Layer Territorio Comunale!!!!
                continue

            layers_scan.append (row[0])

            arcpy.AddMessage(str(row))
            layer_id = row[0]
            row_desc = dict(decodifica[str(layer_id)])

            if parte and row_desc["z_omogenea"]:
                parte_suff = "ad " if row_desc["definizione"][0].upper() == "A" else "a "
                parte_txt = "Parte " + parte_suff
            else:
                parte_txt = ""

            row_desc["layer"] = layer_id
            row_desc["definizione"] = parte_txt + row_desc["definizione"]
            row_desc["note"] = row[1]
            row_desc["interno_pe"] = row[2]
            row_desc["area"] = row[3]
            
            #arcpy.AddMessage("%s %s %s" % (check_layer,check_layer_list[0], str(check_layer == check_layer_list[0])))
            #if check_layer == check_layer_list[0]:

            if row_desc["z_omogenea"]:
                area_zonizzata += row[3]

            if row_desc["z_omogenea"] in ["b","c"]:
                check_layer_lyr = arcpy.mapping.Layer(check_layer)
                arcpy.SelectLayerByAttribute_management(check_layer_lyr, "NEW_SELECTION", ' "OBJECTID" = %d ' % row[4] )
                #out = arcpy.CopyFeatures_management([particella_union], "part")
                with arcpy.da.SearchCursor(check_layer_lyr, ["SHAPE@", ]) as cursor_zo:
                    for row_zo in cursor_zo:
                        #arcpy.CopyFeatures_management(, "feature_check")
                        res = arcpy.gp.ztoscvol([row_zo[0]])
                del cursor_zo

                arcpy.AddMessage(res.getOutput(0))
                zo = json.loads(res.getOutput(0))
                if zo["copertura"] > 12.5 and zo["indice"] > 1.5:
                    row_desc["z_omogenea"] = "b"
                else:
                    row_desc["z_omogenea"] = "c"
                
            if row_desc["z_omogenea"]:
                if row_desc["z_omogenea"].upper() in zone_scan:
                    zone_scan[row_desc["z_omogenea"].upper()] += row_desc["area"]
                else:
                    zone_scan[row_desc["z_omogenea"].upper()] = row_desc["area"]

            output.append(row_desc)
                
            
    del cursor  

if int(area_totale) != int(area_zonizzata):
    output.append(    {
            "layer": 999, 
            "definizione": "Parte a Viabilità" if parte else "Viabilità", 
            "nome": "Area non zonizzata", 
            "url": "", 
            "gruppo": "cdu", 
            "area": area_totale-area_zonizzata, 
            "note": None, 
            "articolo": "999.999", 
            "interno_pe": 0,
            "z_omogenea": ""
        }
    )

arcpy.AddMessage(json.dumps(output,indent=3))
arcpy.SetParameterAsText(2,json.dumps(output))

zone2006 = arcpy.gp.zto2006(probe_path)
zone = {
    "vigente": zone_scan,
    "2006": json.loads(zone2006.getOutput(0))
}

arcpy.AddMessage(json.dumps(zone,indent=3))
arcpy.SetParameterAsText(3,json.dumps(zone))

arcpy.AddMessage(arcpy.GetParameterAsText(1))
if arcpy.GetParameterAsText(1):
    with open(arcpy.GetParameterAsText(1),"w") as f:
        f.write(json.dumps(output, indent=3))