
# -*- coding: utf-8 -*-

#---------------------------------------------------------------------
# Name:        Script per la generazione di CDU - Comune di Padova
#
# Author:      Enrico Ferreguti
#
# Copyright:   (c) Comune di Padova 2020
#---------------------------------------------------------------------

__version__ = "0.9"
__author__  = "Enrico Ferreguti"
__email__ = "ferregutie@comune.padova.it"
__license__ = "GPLv3"
__copyright__ = "Copyright 2020, Comune di Padova"


# Import system modules
import arcpy
import os
import uuid
import tempfile
import json

from sets import Set

#from SUPPORT import decodifica_pi, decodifica_pat, calc_area_totale, get_jobfile, ext2poly, create_fc

from SUPPORT import current_workspace, memory_workspace, scratch_workspace, activity_workspace, output_workspace, get_jobfile

import SUPPORT
reload(SUPPORT)
decodifica_pi = SUPPORT.decodifica_pi
decodifica_pat = SUPPORT.decodifica_pat
calc_area_totale = SUPPORT.calc_area_totale
get_jobfile = SUPPORT.get_jobfile
ext2poly = SUPPORT.ext2poly
create_fc = SUPPORT.create_fc

class CDUPItool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "CDU-PI"
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

        out_json = arcpy.Parameter(
            displayName="Risultato",
            name="out_json",
            datatype="DEFile",
            parameterType="Optional",
            direction="Output")

        params = [in_features, out_txt, out_zone]

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
                intersect_layer = os.path.join(scratch_workspace,"buffer_%s" % uuid.uuid4().hex)
                arcpy.Buffer_analysis(check_layer, intersect_layer, "0.1")
            inFeatures = [probe_path, check_layer]
            #intersectOutput = os.path.join(scratch_workspace,"IntersectOutputResult_%s" % uuid.uuid4().hex)
            intersectOutput = get_jobfile("memory")
            clusterTolerance = 0    
            arcpy.Intersect_analysis(inFeatures, intersectOutput, "", clusterTolerance, "input")
            
            check = arcpy.Describe(intersectOutput)
            field_names = [f.name for f in arcpy.ListFields(intersectOutput)]
            arcpy.AddMessage("field_check: %s" % str(field_names))

            #zone check
            with arcpy.da.SearchCursor(intersectOutput, ["LAYER", "NOTE", "INTERNO_PER", "SHAPE@area", "OID"]) as cursor:  
                for row in cursor: 
                    if decodifica_pi[str(row[0])]["z_omogenea"]:
                        zone_check.add(row[0])
            arcpy.AddMessage("zone_check: %s" % str(zone_check))
            if len(zone_check) > 1:
                parte = True
            else:
                parte = False
            
            with arcpy.da.SearchCursor(intersectOutput, ["LAYER", "NOTE", "INTERNO_PER", "SHAPE@area", "OID"]) as cursor:  
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
                        arcpy.SelectLayerByAttribute_management(check_layer_lyr, "NEW_SELECTION", ' "OBJECTID" = %d ' % row[4] ) #OBJECTID
                        #arcpy.AddMessage(dir(arcpy.gp.toolbox))
                        with arcpy.da.SearchCursor(check_layer_lyr, ["SHAPE@", ]) as cursor_zo:
                            for row_zo in cursor_zo:
                                res = arcpy.gp.ZTOSCVOLTool([row_zo[0]])
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
        parameters[1].value = json.dumps(output)

        zone2006 = arcpy.gp.ZTO2006Tool(probe_path)
        zone = {
            "vigente": zone_scan,
            "2006": json.loads(zone2006.getOutput(0))
        }

        arcpy.AddMessage(json.dumps(zone,indent=3))
        parameters[2].value = json.dumps(zone)

        #if parameters[1].valueAsText:
        #    with open(parameters[1].valueAsText,"w") as f:
        #        f.write(json.dumps(output, indent=3))


class CDUPATtool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "CDU-PAT"
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

        out_txt = arcpy.Parameter(
            displayName="Risultato text",
            name="out_txt",
            datatype="GPString",
            parameterType="Derived",
            direction="Output")

        out_json = arcpy.Parameter(
            displayName="Risultato json",
            name="out_json",
            datatype="DEFile",
            parameterType="Optional",
            direction="Output")

        out_fc = arcpy.Parameter(
            displayName="Risultato text",
            name="out_txt",
            datatype="GPString",
            parameterType="Derived",
            direction="Output")

        params = [in_features, out_txt]

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
                        #intersect_layer = os.path.join(memory_workspace,"buffer_%s" % uuid.uuid4().hex)
                        intersect_layer = get_jobfile("memory")
                        arcpy.Buffer_analysis(check_layer, intersect_layer, "0.1")
                    
                    target_lyr = arcpy.mapping.Layer(intersect_layer)
                    if related["campo"]:
                        target_lyr.definitionQuery = "%s = '%s'" % (related["campo"], related["valore"])
                    
                    inFeatures = [probe_path, target_lyr]
                    #intersectOutput = os.path.join(memory_workspace,"IntersectOutputResult_%s" % uuid.uuid4().hex)
                    intersectOutput = get_jobfile("memory")
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

        parameters[1].value = json.dumps(output)

        #if parameters[1].valueAsText:
        #    with open(parameters[1].valueAsText, "w") as f:
        #        f.write(json.dumps(output, indent=3))


class CDUCStool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "CDU-CS"
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

        out_txt = arcpy.Parameter(
            displayName="output txt",
            name="out_txt",
            datatype="GPString",
            parameterType="Derived",
            direction="Output")

        out_json = arcpy.Parameter(
            displayName="output json",
            name="out_json",
            datatype="DEFile",
            parameterType="Optional",
            direction="Output")

        params = [in_features, tolleranza, out_txt]
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
            #intersectOutput = os.path.join(memory_workspace,"IntersectOutputResult_%s" % uuid.uuid4().hex)
            intersectOutput = get_jobfile("memory")
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

        parameters[2].value = json.dumps(output)

        #if parameters[2].valueAsText:
        #    with open(parameters[2].valueAsText,"w") as f:
        #        f.write(json.dumps(output, indent=3))

class CC2FCtool(object):
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

        #input_lyr_name = os.path.join(memory_workspace, "filter_" + uuid.uuid4().hex)
        #output_lyr_name = os.path.join(scratch_workspace, "catasto_" + uuid.uuid4().hex)
        input_lyr_name = get_jobfile("memory")
        output_lyr_name = get_jobfile("memory")

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

        #out_lyr = arcpy.mapping.Layer(output_lyr_name)
        #out_lyr.name = "ricerca catastale %s" % arcpy.GetParameterAsText(0)

        #esrijson_filepath = os.path.join(tempfile.mkdtemp(),'catasto.json')
        esrijson_filepath = get_jobfile("output","json")

        with open(esrijson_filepath,'w') as f:
            f.write(particella_union.JSON)
            
        arcpy.AddMessage(esrijson_filepath)

        parameters[1].value = output_lyr_name
        parameters[2].value = esrijson_filepath




class DBTextractTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "DBT-2-DXF"
        self.description = "da scrivere"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """
        Define parameter definitions
        https://pro.arcgis.com/en/pro-app/arcpy/geoprocessing_and_python/defining-parameter-data-types-in-a-python-toolbox.htm
        """

        extent = arcpy.Parameter(
            displayName="Extent",
            name="in_features",
            datatype="GPExtent",
            parameterType="Required",
            direction="Input")

        srs = arcpy.Parameter(
            displayName="Spatial reference",
            name="srs",
            datatype="GPSpatialReference",
            parameterType="Optional",
            direction="Input")

        out_geojson = arcpy.Parameter(
            displayName="Output geojson",
            name="out_json",
            datatype="GPString",
            parameterType="Derived",
            direction="Output")

        out_dxf = arcpy.Parameter(
            displayName="Output dxf",
            name="out_dxf",
            datatype="DEFile",
            parameterType="Derived",
            direction="Output")

        out_lyr = arcpy.Parameter(
            displayName="Output lyr",
            name="out_lyr",
            datatype="GPFeatureLayer",
            parameterType="Derived",
            direction="Output")

        params = [extent, srs, out_geojson, out_dxf, out_lyr]

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


        arcpy.ImportToolbox(os.path.join(os.path.dirname(__file__), "URB.pyt"))
        arcpy.gp.toolbox = os.path.join(os.path.dirname(__file__), "URB.pyt")

        extent = parameters[0].value
        srs = parameters[1].value

        arcpy.AddMessage("control: %s %s" % (extent, srs))

        ext_poly = ext2poly(extent, arcpy.SpatialReference(3003))
            
        sel_fc = create_fc(ws="scratch")
        ext_fc_cursor = arcpy.da.InsertCursor(sel_fc,("SHAPE@"))
        ext_fc_cursor.insertRow([ext_poly])
        del ext_fc_cursor

        sel_lyr = arcpy.mapping.Layer(sel_fc)
        arcpy.AddMessage("sel_lyr: %s" % str(sel_lyr))

        check_layer_list = [
            [r"Connessioni database\VISIO_R_GDBT.sde\SIT.DBTOPOGRAFICO\SIT.UN_VOL", "UN_VOL_AV", 0],
            [r"Connessioni database\VISIO_R_GDBT.sde\SIT.DBTOPOGRAFICO\SIT.AATT", "", 1],
            [r"Connessioni database\VISIO_R_GDBT.sde\SIT.DBTOPOGRAFICO\SIT.MN_EDI_NOVOL", "", 2],
            [r"Connessioni database\VISIO_R_GDBT.sde\SIT.DBTOPOGRAFICO\SIT.MN_UVOL", "MN_UVO_ALT", 3],
            [r"Connessioni database\VISIO_R_GDBT.sde\SIT.DBTOPOGRAFICO\SIT.AR_VRD", "", 4],
            #[r"Connessioni database\VISIO_R_GDBT.sde\SIT.DBTOPOGRAFICO\SIT.AR_MARC", "", 5],
            #[r"Connessioni database\VISIO_R_GDBT.sde\SIT.DBTOPOGRAFICO\SIT.AC_VEI", "", 6],
            [r"Connessioni database\VISIO_R_GDBT.sde\SIT.DBTOPOGRAFICO\SIT.CL_AGR", "", 7],
            [r"Connessioni database\VISIO_R_GDBT.sde\SIT.DBTOPOGRAFICO\SIT.A_PED", "", 8],
            [r"Connessioni database\VISIO_R_GDBT.sde\SIT.DBTOPOGRAFICO\SIT.PS_INC", "", 9],
        ]

            
        sel_fc = get_jobfile("memory")
        sel_fc_fields = (  
            ("Layer", "TEXT", None, None, 10, "", "NULLABLE", "NON_REQUIRED"),  
            ("Color", "SHORT", None, None, None, "", "NULLABLE", "NON_REQUIRED"),  
            ("TxtValue", "TEXT", None, None, 10, "", "NULLABLE", "NON_REQUIRED"), 
        ) 
        intersectOutput_clean = create_fc("memory", fields=sel_fc_fields)

        sel_note = get_jobfile("memory")
        sel_note_fields = (  
            ("Layer", "TEXT", None, None, 50, "", "NULLABLE", "NON_REQUIRED"),  
            ("Color", "SHORT", None, None, None, "", "NULLABLE", "NON_REQUIRED"),  
            ("TxtValue", "TEXT", None, None, 255, "", "NULLABLE", "NON_REQUIRED"), 
            ("CADType", "TEXT", None, None, 50, "", "NULLABLE", "NON_REQUIRED"), 
        ) 
        intersectOutput_note = create_fc("memory", fields=sel_note_fields, geom_type="POINT")
        cursor_note = arcpy.da.InsertCursor(intersectOutput_note, ("Layer", "Color", "TxtValue", "CADType", "SHAPE@"))

        for check_layer_def in check_layer_list:
            check_layer = check_layer_def[0]
            arcpy.AddMessage("check_layer: %s" % check_layer)
            desc = arcpy.Describe(check_layer)
            inFeatures = [ check_layer, sel_lyr ]
            intersectOutput = get_jobfile("memory")
            clusterTolerance = 0    
            arcpy.Intersect_analysis(inFeatures, intersectOutput, "", clusterTolerance, "input")

            if check_layer_def[1]:
                field_def = ("Layer", "Color", "TxtValue", "SHAPE@")
                check_def = [check_layer_def[1], "SHAPE@"]
            else:
                field_def = ("Layer", "Color", "SHAPE@")
                check_def = ["SHAPE@"]

            cursor_clean = arcpy.da.InsertCursor(intersectOutput_clean,field_def)

            with arcpy.da.SearchCursor(intersectOutput, check_def) as cursor:
                for row in cursor:
                    if check_layer_def[1]:
                        row_def = [desc.name.replace("SIT.",""), check_layer_def[2], str(row[0]), cursor[1]]
                        note_def = row_def[:-1] + ["TEXT", arcpy.PointGeometry(cursor[1].centroid)]
                        cursor_note.insertRow(note_def)
                    else:
                        row_def = [desc.name.replace("SIT.",""), check_layer_def[2], cursor[0]]
                    cursor_clean.insertRow(row_def)
            
        del cursor_clean
        del cursor_note


        extraction_json_filepath = get_jobfile("output","json")
        arcpy.FeaturesToJSON_conversion(intersectOutput_clean, extraction_json_filepath, format_json=True, geoJSON=True)

        arcpy.AddMessage(extraction_json_filepath)
        parameters[2].value = extraction_json_filepath

        extraction_dxf_filepath = get_jobfile("output","dxf")
        arcpy.ExportCAD_conversion([intersectOutput_clean, intersectOutput_note], "DXF_R2004", extraction_dxf_filepath, "USE_FILENAMES_IN_TABLES", "OVERWRITE_EXISTING_FILES", "")
        parameters[3].value = extraction_dxf_filepath

        lyr = arcpy.mapping.Layer(intersectOutput_clean)
        parameters[4].value = intersectOutput_clean

        #if parameters[1].valueAsText:
        #    with open(parameters[1].valueAsText,"w") as f:
        #        f.write(json.dumps(output, indent=3))