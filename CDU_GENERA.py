
# Import arcpy module
import arcpy

# Load required toolboxes

# Local variables:
coordinate_catastali = arcpy.GetParameterAsText(0)
protocollo_numero = arcpy.GetParameterAsText(1)
protocollo_data = arcpy.GetParameterAsText(2)
odt_target = arcpy.GetParameterAsText(3)

json = ""
poligono = ""
output_json = ""
output_testo_PI = ""
output_json__2_ = ""
output_testo_PAT = ""

# Process: da coordinate catastali a layertemporaneo

# Warning: the toolbox C:/Users/ferregutie/AppData/Roaming/ESRI/Desktop10.6/ArcToolbox/My Toolboxes/URBAN.tbx DOES NOT have an alias. 
# Please assign this toolbox an alias to avoid tool name collisions
# And replace arcpy.gp.coordinateCatastaliToLayer(...) with arcpy.coordinateCatastaliToLayer_ALIAS(...)

arcpy.AddMessage("STAGE1")

arcpy.ImportToolbox("C:/Users/ferregutie/AppData/Roaming/ESRI/Desktop10.6/ArcToolbox/My Toolboxes/URBAN.tbx")
arcpy.gp.toolbox = "C:/Users/ferregutie/AppData/Roaming/ESRI/Desktop10.6/ArcToolbox/My Toolboxes/URBAN.tbx"

CC_result = arcpy.gp.coordinateCatastaliToLayer(coordinate_catastali)
arcpy.AddMessage("CC_result: %s" % CC_result)

# Process: CDU_PI
PI_result = arcpy.gp.CDUPI(CC_result, output_json)
arcpy.AddMessage("PI_result: %s" % str(PI_result))
'''
# Process: CDU_CS
CS_result = arcpy.gp.CDUCS(poligono, output_json)
arcpy.AddMessage("CS_result: %s" % str(CS_result))

# Process: CDU_PAT
PAT_result = arcpy.gp.CDUPAT(poligono, output_json__2_)
arcpy.AddMessage("PAT_result: %s" % str(PAT_result))
'''
