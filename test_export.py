# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# test_export.py
# Created on: 2020-01-10 10:28:43.00000
#   (generated by ArcGIS/ModelBuilder)
# Description: 
# ---------------------------------------------------------------------------

# Import arcpy module
import arcpy

# Load required toolboxes
arcpy.ImportToolbox("D:/Documents/01_LAVORO/00-REPERTORI/99_ESRI/ESRI.CDU_SCRIPTS/toolbox/URB.pyt")


# Local variables:
Risultato = ""

# Process: ZTO_SC_VOL
arcpy.gp.toolbox = "D:/Documents/01_LAVORO/00-REPERTORI/99_ESRI/ESRI.CDU_SCRIPTS/toolbox/URB.pyt";
# Warning: the toolbox D:/Documents/01_LAVORO/00-REPERTORI/99_ESRI/ESRI.CDU_SCRIPTS/toolbox/URB.pyt DOES NOT have an alias. 
# Please assign this toolbox an alias to avoid tool name collisions
# And replace arcpy.gp.ZTO_SC_VOL_Tool(...) with arcpy.ZTO_SC_VOL_Tool_ALIAS(...)
arcpy.gp.ZTO_SC_VOL_Tool("")

