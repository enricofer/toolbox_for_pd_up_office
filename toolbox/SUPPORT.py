
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


import json
import os
import arcpy
import uuid
import tempfile


current_workspace = arcpy.env.workspace
memory_workspace = "in_memory"
scratch_workspace = arcpy.env.scratchWorkspace

#activity_workspace = "E:\\acrgisserver\\directories\\arcgisjobs\\CDUtool"
#output_workspace = "E:\\acrgisserver\\directories\\arcgisoutput\\CDUtool"

activity_workspace = "D:\\Documents\\01_LAVORO\\99-sandbox\\CDUtool"
output_workspace = "D:\\Documents\\01_LAVORO\\99-sandbox\\CDUtool"

with open(os.path.join(os.path.dirname(__file__),"sit_decodifica_con_descrizioni.json"), 'r') as f:
    decodifica_pi = json.load(f)

with open(os.path.join(os.path.dirname(__file__),"sit_decodifica_pat.json"), 'r') as f:
    decodifica_pat = json.load(f)

def calc_area_totale(fc_path):
    area_totale = 0
    with arcpy.da.SearchCursor(fc_path, ["SHAPE@area"]) as cursor:  
        for row in cursor:  
            area_totale += row[0]
    return area_totale

def get_ws_dir (ws):
    if ws == "temp":
        ws_dir = tempfile.mkdtemp()
    else:
        ws_dir = globals()[ws + "_workspace"]

    if ws in ("activity", "output") and not os.path.exists(ws_dir):
        os.makedirs(ws_dir)
    return ws_dir

def get_jobfile(ws, ext=""):
    if ext:
        ext = "." + ext

    jobfile_path = os.path.join(get_ws_dir(ws),"job_" + uuid.uuid4().hex + ext)
    return jobfile_path
    
def ext2poly(ext, sr=None):
    BL = arcpy.Point(ext.XMin,ext.YMin) # bottom left  
    BR = arcpy.Point(ext.XMax,ext.YMin) # bottom right  
    TR = arcpy.Point(ext.XMax,ext.YMax) # top right  
    TL = arcpy.Point(ext.XMin,ext.YMax) # top left  
    df_poly = arcpy.Polygon(arcpy.Array([[BL,BR,TR,TL,BL]]),sr) # create polygon  
    return df_poly

def create_fc (ws="memory", sr=3003, geom_type="POLYGON", fields=None):
    fc = arcpy.management.CreateFeatureclass(get_ws_dir(ws), "job_" + uuid.uuid4().hex, geom_type, spatial_reference=sr)
    if fields:
        for field in fields:
            arcpy.AddField_management(fc, *field)
    return fc[0]