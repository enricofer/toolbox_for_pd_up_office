
# -*- coding: utf-8 -*-

# Import arcpy module
import arcpy
import json as json_module
import tempfile
import os

from secretary import Renderer

def decodificaCatasto(coordinate_catastali):
    FMs = coordinate_catastali.split(' ',)
    out = ''
    for FM in FMs:
        decodeFM = FM.split('/')
        if decodeFM[0] != FM:
            if len(decodeFM[1].split('-')) == 1:
                mappaleDesc = 'MAPPALE'
            else:
                mappaleDesc = 'MAPPALI'
            out += ' FOGLIO '+ decodeFM[0]
            out += ' %s %s'% (mappaleDesc,decodeFM[1])
    return out

# Local variables:
contesto = arcpy.GetParameterAsText(0)
coordinate_catastali = arcpy.GetParameterAsText(1)
protocollo_numero = arcpy.GetParameterAsText(2)
protocollo_data = arcpy.GetParameterAsText(3)
richiedente = arcpy.GetParameterAsText(4)
odt_target = arcpy.GetParameterAsText(5)


#json = ""
poligono = ""
output_json = ""
output_testo_PI = ""
output_json__2_ = ""
output_testo_PAT = ""

test = False
PI_test = '''
[
    {"note": null, "articolo": 0, "layer": 0, "definizione": "Area totale", "nome": "Area totale", "url": "", "gruppo": "cdu", "area": 3978.322295527004, "interno_pe": 0}, 
    {"layer": 39, "definizione": "Area interessata da vincolo aeroportuale disciplinato dalla L. 4 febbraio 1963 n.58", "nome": "Perimetro ricognitivo aeroportuale", "url": "http://www.padovanet.it/allegati/C_1_Allegati_15388_Allegato_0.pdf", "gruppo": "perimetri", "area": 2974.954930029389, "note": null, "articolo": "", "interno_pe": null}, 
    {"layer": 39, "definizione": "Area interessata da vincolo aeroportuale disciplinato dalla L. 4 febbraio 1963 n.58", "nome": "Perimetro ricognitivo aeroportuale", "url": "http://www.padovanet.it/allegati/C_1_Allegati_15388_Allegato_0.pdf", "gruppo": "perimetri", "area": 2974.954930029389, "note": null, "articolo": "", "interno_pe": null}, 
    {"layer": 56, "definizione": "Zona di degrado %", "nome": "Perimetro zone di degrado", "url": "http://www.padovanet.it/allegati/C_1_Allegati_15388_Allegato_0.pdf#92", "gruppo": "centro_storico", "area": 1003.3676370044367, "note": null, "articolo": 41, "interno_pe": 0}, 
    {"layer": 39, "definizione": "Area interessata da vincolo aeroportuale disciplinato dalla L. 4 febbraio 1963 n.58", "nome": "Perimetro ricognitivo aeroportuale", "url": "http://www.padovanet.it/allegati/C_1_Allegati_15388_Allegato_0.pdf", "gruppo": "perimetri", "area": 1003.3676370044367, "note": null, "articolo": "", "interno_pe": null}, 
    {"layer": 39, "definizione": "Area interessata da vincolo aeroportuale disciplinato dalla L. 4 febbraio 1963 n.58", "nome": "Perimetro ricognitivo aeroportuale", "url": "http://www.padovanet.it/allegati/C_1_Allegati_15388_Allegato_0.pdf", "gruppo": "perimetri", "area": 1003.3676370044367, "note": null, "articolo": "", "interno_pe": null}, 
    {"note": null, "articolo": "999.999", "layer": 999, "definizione": "Viabilità", "nome": "Area non zonizzata", "url": "", "gruppo": "cdu", "area": 3978.322295527004, "interno_pe": 0}]
'''
CS_test = u'''
[{"norma1": "UNITA' DI PIANO DELLA CLASSE E     MODALITA' DI TIPO E - RISTRUTTURAZIONE EDILIZIA", "area": 3953.5930837093556, "despro1": "RESIDENZIALE, COMMERCIALE, DIREZIONALE, TURISTICA E ARTIGIANALE", "full_id": "0026500014", "despro": " "}]
'''
PAT_test = u'''
[
    {"nta": 5.1, "layer": "b0101011_vincolo", "fc": "SIT.b0101011_Vincolo_r", "desc": "Vincolo sui beni culturali  (D.Lgs. 42/2004, artt.10 e 12)"}, 
    {"nta": "5.6.12", "layer": "b0105021_fascerispetto", "fc": "SIT.b0105021_FasceRispetto_r", "desc": "Servitù o Fasce di rispetto aeroportuale"}, 
    {"nta": "5.5.1", "layer": "b0104011_centrostorico", "fc": "SIT.b0104011_CentroStorico_r", "desc": "Centro Storico (P.R.G., P.T.C.P. art.26 A N.T., P.T.R.C. art.24 N.T.)"}, 
    {"nta": "5.6.8.1", "layer": "b0105051_centriabitati", "fc": "SIT.b0105051_CentriAbitati_r", "desc": "Centri Abitati"}
]
'''

arcpy.ImportToolbox("C:/Users/ferregutie/AppData/Roaming/ESRI/Desktop10.6/ArcToolbox/My Toolboxes/URBAN.tbx")
arcpy.gp.toolbox = "C:/Users/ferregutie/AppData/Roaming/ESRI/Desktop10.6/ArcToolbox/My Toolboxes/URBAN.tbx"

if test:
    identificazione = "TEST"
    PI_def = json_module.loads(PI_test)
    CS_def = json_module.loads(CS_test)
    PAT_def = json_module.loads(PAT_test)
    arcpy.AddMessage(str(PAT_def))
    for item in PAT_def:
        arcpy.AddMessage(item['desc'])
else:
    poligono = contesto
    identificazione = ""

    if coordinate_catastali:
        CC_result = arcpy.gp.coordinateCatastaliToLayer(coordinate_catastali)
        arcpy.AddMessage("CC_result: %s" % CC_result.getOutput(0))
        poligono = CC_result.getOutput(0)
        identificazione = u"così individuata nel Catasto Terreni: %s" % decodificaCatasto(coordinate_catastali)
    else:
        if not contesto:
            arcpy.AddError("Deve essere specificata almeno un contesto, come layer o come coordinate catastali")
            exit(0)
        poligono = contesto

    # Process: CDU_PI
    PI_result = arcpy.gp.CDUPI(poligono, output_json)
    arcpy.AddMessage("PI_result: %s" % PI_result.getOutput(1))
    PI_def = json_module.loads(PI_result.getOutput(1))

    checkInCS = False
    for defin in PI_def:
        if defin["layer"] == 55:
            checkInCS = True

    if checkInCS:
        # Process: CDU_CS
        CS_result = arcpy.gp.CDUCS(poligono, output_json)
        arcpy.AddMessage("CS_result: %s" % CS_result.getOutput(1))
        CS_def = json_module.loads(CS_result.getOutput(1))
    else:
        CS_def = []

    # Process: CDU_PAT
    PAT_result = arcpy.gp.CDUPAT(poligono, output_json__2_)
    arcpy.AddMessage("PAT_result: %s" % PAT_result.getOutput(1))
    PAT_def = json_module.loads(PAT_result.getOutput(1))

PI_desc = ''
PI_nta = ''
dest_selection = []
for item in PI_def:
    arcpy.AddMessage("item: %s" % str(item))
    if item["layer"] != 0 and not item["layer"] in dest_selection:
        dest_selection.append(item["layer"])
        if '%' in item["definizione"]:
            definizione = item["definizione"].replace('%', unicode(item["note"] or ""))
        else:
            definizione = item["definizione"]
        PI_desc += '%s, ' % definizione.upper()
        PI_nta += '%s, ' % str(item["articolo"]).upper()
PI_desc = PI_desc[:-2] + "; "
PI_nta = PI_nta[:-2] + "; "

CS_udp = ''
dest_selection = []
for item in CS_def:
    if not item["norma1"]+item["despro1"] in dest_selection:
        dest_selection.append(item["norma1"]+item["despro1"])
        CS_udp += '%s con destinazione %s, ' % (item['norma1'], item["despro1"])
CS_udp = CS_udp[:-2] + "; "

PAT_desc = ''
PAT_nta = ''
dest_selection = []
for item in PAT_def:
    arcpy.AddMessage("dest_selection: %s" % str(dest_selection))
    if not item["desc"] in dest_selection:
        dest_selection.append(item["desc"])
        PAT_desc += '%s, ' % item["desc"].upper()
        PAT_nta += '%s, ' % str(item["nta"]).upper()
PAT_desc = PAT_desc[:-2] + "; "
PAT_nta = PAT_nta[:-2] + "; "

params = {
    "protocollo": {
        "numero": str(protocollo_numero),
        "data": str(protocollo_data)
    },
    "richiedente": richiedente,
    "pi": {
        "desc": PI_desc,
        "nta": PI_nta
    },
    "cs": CS_udp,
    "pat": {
        "desc": PAT_desc,
        "nta": PAT_nta
    },
}

arcpy.AddMessage("PARAMS: %s" % str(params))

engine = Renderer()
template2 = os.path.join(os.path.dirname(__file__),"SOMMARIO_template.odt")
result2 = engine.render(template2, PI_def=PI_def, CS_def=CS_def, PAT_def=PAT_def)
sommario_target = os.path.join(tempfile.mkdtemp(),"sommario.odt")

with open(sommario_target,'wb') as output:
    output.write(result2)
    output.flush()

arcpy.AddMessage("SOMMARIO DESTINAZIONI: %s" % sommario_target)

if not odt_target:
    odt_target = os.path.join(tempfile.mkdtemp(),"CDU.odt")

template1 = os.path.join(os.path.dirname(__file__),"CDU_template.odt")
result1 = engine.render(template1, **params)

with open(odt_target,'wb') as output:
    output.write(result1)
    output.flush()

arcpy.AddMessage("SOMMARIO DESTINAZIONI: %s" % odt_target)


