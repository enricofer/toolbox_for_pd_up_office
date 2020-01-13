
# -*- coding: utf-8 -*-
# Import system modules
import arcpy
import os
import uuid
import tempfile
import json

from sets import Set

from SUPPORT import decodifica_pi, decodifica_pat, calc_area_totale

class CDU_PI_tool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "CDU_PI"
        self.description = "da scrivere"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """
        Define parameter definitions
        https://pro.arcgis.com/en/pro-app/arcpy/geoprocessing_and_python/defining-parameter-data-types-in-a-python-toolbox.htm
        """

        in_features = arcpy.Parameter(
            displayName="Input",
            name="in_features",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")

        out_json = arcpy.Parameter(
            displayName="Risultato",
            name="out_json",
            datatype="DEFile",
            parameterType="Optional",
            direction="Output")

        out_txt = arcpy.Parameter(
            displayName="Risultato",
            name="out_txt",
            datatype="GPString",
            parameterType="Derived",
            direction="Output")

        out_zone = arcpy.Parameter(
            displayName="Risultato",
            name="out_zone",
            datatype="GPString",
            parameterType="Derived",
            direction="Output")

        params = [in_features, out_json, out_txt, out_zone]

        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        arcpy.AddMessage("default.gdb_path: %s" % arcpy.env.workspace)
        #default_workspace = arcpy.env.scratchWorkspace
        default_workspace = "in_memory"
        current_workspace = arcpy.env.scratchWorkspace

        arcpy.ImportToolbox(os.path.join(os.path.dirname(__file__), "URB.pyt"))
        arcpy.gp.toolbox = os.path.join(os.path.dirname(__file__), "URB.pyt")

        probe_path = parameters[0].valueAsText

        check_layer_list = [
            r"Connessioni database\VISIO_R_GDBT.sde\SIT.PI\SIT.PI_zoning",
            r"Connessioni database\VISIO_R_GDBT.sde\SIT.PI\SIT.PI_perimetri",
            r"Connessioni database\VISIO_R_GDBT.sde\SIT.PI\SIT.PI_linee",
            r"Connessioni database\VISIO_R_GDBT.sde\SIT.PI\SIT.PI_limiti",
        ]

        area_totale = calc_area_totale(probe_path)
        area_zonizzata = 0

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
                    if decodifica_pi[str(row[0])]["z_omogenea"]:
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
                    row_desc = dict(decodifica_pi[str(layer_id)])

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
                        arcpy.AddMessage(dir(arcpy.gp.toolbox))
                        with arcpy.da.SearchCursor(check_layer_lyr, ["SHAPE@", ]) as cursor_zo:
                            for row_zo in cursor_zo:
                                res = arcpy.gp.ZTO_SC_VOL_Tool([row_zo[0]])
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
        parameters[2].value = json.dumps(output)

        zone2006 = arcpy.gp.ZTO_2006_Tool(probe_path)
        zone = {
            "vigente": zone_scan,
            "2006": json.loads(zone2006.getOutput(0))
        }

        arcpy.AddMessage(json.dumps(zone,indent=3))
        parameters[3].value = json.dumps(zone)

        if parameters[1].valueAsText:
            with open(parameters[1].valueAsText,"w") as f:
                f.write(json.dumps(output, indent=3))


class CDU_PAT_tool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "CDU_PAT"
        self.description = "da scrivere"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """
        Define parameter definitions
        https://pro.arcgis.com/en/pro-app/arcpy/geoprocessing_and_python/defining-parameter-data-types-in-a-python-toolbox.htm
        """

        in_features = arcpy.Parameter(
            displayName="Input",
            name="in_features",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")

        out_json = arcpy.Parameter(
            displayName="Risultato json",
            name="out_json",
            datatype="DEFile",
            parameterType="Optional",
            direction="Output")

        out_txt = arcpy.Parameter(
            displayName="Risultato text",
            name="out_txt",
            datatype="GPString",
            parameterType="Derived",
            direction="Output")

        params = [in_features, out_json, out_txt]

        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""

        def clean_fc(name):
            return name.lower().replace("sit.","").replace("_rw","").replace("_r","")
            
        def extract_related(selector,all_list):
            lyrs = []
            for item in all_list:
                if item["layer"].lower() == selector:
                    item["clean_layer"] = item["layer"].lower()
                    lyrs.append(item)
            return lyrs

        arcpy.AddMessage("default.gdb_path: %s" % arcpy.env.workspace)

        current_workspace = arcpy.env.scratchWorkspace
        default_workspace = "in_memory"

        probe_path = parameters[0].valueAsText

        cleaned_decodifica = [clean_fc(item["layer"]) for item in decodifica_pat]

        arcpy.AddMessage("cleaned_decodifica: %s" % str(cleaned_decodifica))

        base_pat_repository = r"Connessioni database\VISIO_R_GDBT.sde\SIT.PAT_r"
        arcpy.env.workspace = base_pat_repository
        check_layer_list = arcpy.ListFeatureClasses("*")

        area_totale = calc_area_totale(probe_path)

        arcpy.AddMessage("area totale: %d" % area_totale)

        # Set the workspace (to avoid having to type in the full path to the data every time)
        #arcpy.env.workspace = r"Connessioni database\VISIO_R_GDBT.sde\SIT.PI"
        # Process: Find all stream crossings (points)
            
        output = []

        for check_layer in check_layer_list:
            arcpy.AddMessage("check_layer: %s, %s, %s" % (check_layer,clean_fc(check_layer),str(clean_fc(check_layer) in cleaned_decodifica)))
            desc = arcpy.Describe(check_layer)
            
            if clean_fc(check_layer) in cleaned_decodifica:
                related_list = extract_related(clean_fc(check_layer),decodifica_pat)
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

        parameters[2].value = json.dumps(output)

        if parameters[1].valueAsText:
            with open(parameters[1].valueAsText, "w") as f:
                f.write(json.dumps(output, indent=3))


class CDU_CS_tool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "CDU_CS"
        self.description = "da scrivere"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """
        Define parameter definitions
        https://pro.arcgis.com/en/pro-app/arcpy/geoprocessing_and_python/defining-parameter-data-types-in-a-python-toolbox.htm
        """

        in_features = arcpy.Parameter(
            displayName="Input",
            name="in_features",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")

        tolleranza = arcpy.Parameter(
            displayName="Tolleranza",
            name="tolleranza",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        tolleranza.value = 1

        out_json = arcpy.Parameter(
            displayName="output json",
            name="out_json",
            datatype="DEFile",
            parameterType="Optional",
            direction="Output")

        out_txt = arcpy.Parameter(
            displayName="output txt",
            name="out_txt",
            datatype="GPString",
            parameterType="Derived",
            direction="Output")

        params = [in_features, tolleranza, out_json, out_txt]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""

        current_workspace = arcpy.env.scratchWorkspace
        default_workspace = "in_memory"

        probe_path = parameters[0].valueAsText
        tolleranza = float(parameters[1].valueAsText)

        check_layer_list = [
            r"Connessioni database\VISIO_R_GDBT.sde\FERREGUTIE.CS_unitaDiPiano",
        ]

        area_totale = calc_area_totale(probe_path)

        output = []

        for check_layer in check_layer_list:
            arcpy.AddMessage("check_layer: %s" % check_layer)
            inFeatures = [probe_path, check_layer]
            intersectOutput = os.path.join(default_workspace,"IntersectOutputResult_%s" % uuid.uuid4().hex)
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

        parameters[3].value = json.dumps(output)

        if parameters[2].valueAsText:
            with open(parameters[2].valueAsText,"w") as f:
                f.write(json.dumps(output, indent=3))

class CC2FC_tool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "CC2FC"
        self.description = "da scrivere"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """
        Define parameter definitions
        https://pro.arcgis.com/en/pro-app/arcpy/geoprocessing_and_python/defining-parameter-data-types-in-a-python-toolbox.htm
        """

        coordinate_catastali = arcpy.Parameter(
            displayName="Coordinate catastali",
            name="coordinate_catastali",
            datatype="GPString",
            parameterType="Required",
            direction="Input")

        fc_output = arcpy.Parameter(
            displayName="FC output",
            name="fc_output",
            datatype="GPFeatureLayer",
            parameterType="Derived",
            direction="Output")

        out_json = arcpy.Parameter(
            displayName="Output json",
            name="out_json",
            datatype="DEFile",
            parameterType="Optional",
            direction="Output")

        params = [coordinate_catastali, fc_output, out_json]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""

        current_env = arcpy.env.scratchWorkspace
        default_env = arcpy.env.workspace
        scratch_env = "in_memory"

        def coordinateCatastaliToWHERE(coordinateCatastali):
            sqlWhere = ""
            fogliMappali = coordinateCatastali.split(" ")
            for foglioMappali in fogliMappali:
                listaFoglio = foglioMappali.split("/")
                foglio = listaFoglio[0]
                if foglio[-1:].isalpha():
                    foglio = "000"[:3-len(foglio[:-1])]+foglio[:-1]+foglio[-1:].upper()
                else:
                    foglio = "000"[:3-len(foglio)]+foglio+"0"
                listaMappali = listaFoglio[1]
                mappali = listaMappali.split("-")
                for mappale in mappali:
                    sqlWhere += "(FOGLIO = '%s' AND MAPPALE ='%s') OR " % (foglio,mappale)
            return sqlWhere[:-4]

        # Script arguments
        try:
            cc_input = coordinateCatastaliToWHERE(parameters[0].valueAsText)
        except:
            arcpy.AddError("Coordinate catastali inserite in modo errato")
            exit(0)
            
        particelle_output = parameters[1].valueAsText

        arcpy.AddMessage("WHERE: %s" % str(cc_input))

        input_lyr_name = os.path.join(scratch_env, "filter_" + uuid.uuid4().hex)
        output_lyr_name = os.path.join(default_env, "catasto_" + uuid.uuid4().hex)

        particelle_cc_layer = r"Connessioni database\VISIO_R_GDBT.sde\SIT.CATASTO\SIT.particelle_cat"

        arcpy.MakeFeatureLayer_management(particelle_cc_layer,input_lyr_name)
        lyr = arcpy.mapping.Layer(input_lyr_name)
        lyr.definitionQuery = cc_input

        particelle = [f[0] for f in arcpy.da.SearchCursor(input_lyr_name,"SHAPE@")]

        arcpy.AddMessage("particelle: %s" % str(particelle))

        if len(particelle) == 1:
            particella_union = particelle[0]
        elif len(particelle) > 1:
            particella_union = particelle[0]
            arcpy.AddMessage("res %s" % particella_union.WKT)
            for particella_idx in range(1,len(particelle)):
                particella = particelle[particella_idx]
                arcpy.AddMessage("particella %d" % particella_idx)
                particella_union = particella_union.union(particella)
        else:
            arcpy.AddError("Nessuna corrispondenza con il catasto aggiornato")
            exit(0)

        out = arcpy.CopyFeatures_management([particella_union], output_lyr_name)

        out_lyr = arcpy.mapping.Layer(output_lyr_name)
        out_lyr.name = "ricerca catastale %s" % arcpy.GetParameterAsText(0)

        esrijson_filepath = os.path.join(tempfile.mkdtemp(),'catasto.json')
        with open(esrijson_filepath,'w') as f:
            f.write(particella_union.JSON)
            
        arcpy.AddMessage(esrijson_filepath)

        parameters[1].value = output_lyr_name
        parameters[2].value = esrijson_filepath


