# -*- coding: utf-8 -*-
import json
import os
import arcpy


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