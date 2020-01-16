# ---------------------------------------------------------------------------
# CC_to_layer.py
# Usage: CC_to_layer <coordinate_catastali>
# Description:
# ---------------------------------------------------------------------------

# Import arcpy module
import arcpy
import os
import uuid
import tempfile

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
    cc_input = coordinateCatastaliToWHERE(arcpy.GetParameterAsText(0))
except:
     arcpy.AddError("Coordinate catastali inserite in modo errato")
     exit(0)
    
particelle_output = arcpy.GetParameterAsText(1)

arcpy.AddMessage("WHERE: %s" % str(cc_input))

default_env = arcpy.env.workspace
scratch_env = arcpy.env.scratchWorkspace

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

out_lyr = arcpy.mapping.Layer(output_lyr_name) #r"in_memory\%s" % output_lyr_name
out_lyr.name = "ricerca catastale %s" % arcpy.GetParameterAsText(0)

#mxd = arcpy.mapping.MapDocument("CURRENT")
#df = arcpy.mapping.ListDataFrames(mxd)[0]
#arcpy.mapping.AddLayer(df,out_lyr)

esrijson_filepath = os.path.join(tempfile.mkdtemp(),'catasto.json')
with open(esrijson_filepath,'w') as f:
    f.write(particella_union.JSON)
    
arcpy.AddMessage(esrijson_filepath)
#arcpy.FeaturesToJSON_conversion(output_lyr_name,esrijson_filepath,"FORMATTED")

arcpy.SetParameter(1, output_lyr_name)
arcpy.SetParameter(2, esrijson_filepath)