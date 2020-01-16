
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

import arcpy
import os
import uuid
import tempfile
import json

from SUPPORT import decodifica_pi, decodifica_pat, get_jobfile

from SUPPORT import current_workspace, memory_workspace, scratch_workspace, activity_workspace, output_workspace, get_jobfile

class ZTO2006Tool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "ZTO2006"
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

        out_result = arcpy.Parameter(
            displayName="Risultato",
            name="out_result",
            datatype="GPString",
            parameterType="Derived",
            direction="Output")

        params = [in_features, out_result]

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

        probe_path = parameters[0].valueAsText

        arcpy.AddMessage("probe_path: %s" % probe_path)

        if not arcpy.Exists(probe_path):
            arcpy.AddError("Ciao")
            raise arcpy.ExecuteError

        check_layer_list = [
            r"Connessioni database\VISIO_R_GDBT.sde\SIT.ZONOM\SIT.FCL_ZONEOM",
        ]

        area_totale = 0

        with arcpy.da.SearchCursor(probe_path, ["SHAPE","SHAPE@area"]) as cursor:  
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
                #intersect_layer = os.path.join(current_workspace,"buffer_%s" % uuid.uuid4().hex)
                intersect_layer = get_jobfile("memory")
                arcpy.Buffer_analysis(check_layer, intersect_layer, "0.1")

            inFeatures = [probe_path, check_layer]
            #intersectOutput = os.path.join(current_workspace,"IntersectOutputResult_%s" % uuid.uuid4().hex)
            intersectOutput = get_jobfile("memory")
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

        parameters[1].value = json.dumps(zone)


class ZTOSCVOLTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "ZTOSCVOL"
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

        out_result = arcpy.Parameter(
            displayName="Risultato",
            name="out_result",
            datatype="GPString",
            parameterType="Derived",
            direction="Output")

        params = [in_features, out_result]

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

        probe_path = parameters[0].valueAsText

        arcpy.AddMessage("probe_path: %s" % probe_path)

        if not arcpy.Exists(probe_path):
            arcpy.AddError("Ciao")
            raise arcpy.ExecuteError

        check_layer_list = [
            r"Connessioni database\VISIO_R_GDBT.sde\SIT.DBTOPOGRAFICO\SIT.UN_VOL",
        ]

        area_totale = 0

        with arcpy.da.SearchCursor(probe_path, ["SHAPE","SHAPE@area"]) as cursor:  
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
        selection = get_jobfile("memory")
        probe_list_lyr = arcpy.CopyFeatures_management(probe_list, selection)

        for check_layer in check_layer_list:
            arcpy.AddMessage("check_layer: %s" % check_layer)
            desc = arcpy.Describe(check_layer)
            arcpy.AddMessage("check_layer type: %s" % desc.shapeType)
            if desc.shapeType == 'Polygon':
                intersect_layer = check_layer
            else:
                #intersect_layer = os.path.join(current_workspace,"buffer_%s" % uuid.uuid4().hex)
                intersect_layer = get_jobfile("memory")
                arcpy.Buffer_analysis(check_layer, intersect_layer, "0.1")

            inFeatures = [probe_list_lyr, check_layer]
            #intersectOutput = os.path.join(current_workspace,"IntersectOutputResult_%s" % uuid.uuid4().hex)
            intersectOutput = get_jobfile("memory")
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

        parameters[1].value = json.dumps(output)
