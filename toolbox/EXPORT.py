
# -*- coding: utf-8 -*-


# Import system modules
import arcpy
import os
import sys

reload(sys)
sys.setdefaultencoding('utf-8')

import urllib
import uuid
import tempfile
import json
import uuid


from secretary import Renderer

from PyPDF2 import PdfFileMerger, PdfFileReader

from jinja2 import Template

base_url = 'http://10.10.20.58/'

CTR1996_DEF = {
        "id":"Ctr 1996",
        "title":"Ctr 1996",
        "opacity":0.69921875,
        #"visibleLayers":[0,2,3,4,5,6,7,8,10,11,13],
        "minScale": 0,
        "maxScale": 0,
        "url":  base_url + "ArcGIS/rest/services/CTR_PRG/MapServer/"
    }

CATASTO_DEF = {
        "id":"Catasto",
        "title":"Catasto",
        "opacity":0.69921875,
        "visibleLayers":[4,6,7],
        "minScale": 0,
        "maxScale": 0,
        "url":  base_url + "ArcGIS/rest/services/catasto/MapServer/"
    }

PI_DEF = {
        "id":"Ctr 1996",
        "title":"Ctr 1996",
        "opacity":0.69921875,
        #"visibleLayers":[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18],
        "visibleLayers":[0,1,2,3,4],
        "minScale": 0,
        "maxScale": 0,
        "url":  base_url + "ArcGIS/rest/services/prg/MapServer"
    }

TOPO_DEF = {
        "id":"Topo",
        "title":"Topo",
        "opacity":0.69921875,
        "visibleLayers":[0],
        "minScale": 0,
        "maxScale": 0,
        "url":  base_url + "ArcGIS/rest/services/base/MapServer"
    }

PI_CS_DEF = {
        "id":"PI Centro Storico",
        "title":"PI Centro Storico",
        "opacity":0.69921875,
        "visibleLayers":[3,4,6,7,9,10,11,12,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30],
        "minScale": 0,
        "maxScale": 0,
        "url":  base_url + "ArcGIS/rest/services/pr1000/MapServer"
    }

PAT_TRASFORMABILITA_DEF = {
        "id":"Pat trasformabilita",
        "title":"Pat trasformabilita",
        "opacity":0.69921875,
        "visibleLayers":[36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68],
        "minScale": 0,
        "maxScale": 0,
        "url":  base_url + "ArcGIS/rest/services/pat/MapServer"
    }

PAT_VINCOLI_DEF = {
        "id":"Pat vincoli",
        "title":"Pat vincoli",
        "opacity":0.69921875,
        "visibleLayers":[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19],
        "minScale": 0,
        "maxScale": 0,
        "url":  base_url + "ArcGIS/rest/services/pat/MapServer"
    }

PAT_FRAGILITA_DEF = {
        "id":"Pat fragilita",
        "title":"Pat fragilita",
        "opacity":0.69921875,
        "visibleLayers":[30,31,32,33,34],
        "minScale": 0,
        "maxScale": 0,
        "url":  base_url + "ArcGIS/rest/services/pat/MapServer"
    }

PAT_INVARIANTI_DEF = {
        "id":"Pat fragilita",
        "title":"Pat fragilita",
        "opacity":0.69921875,
        "visibleLayers":[21,22,23,24,25,26,27,28],
        "minScale": 0,
        "maxScale": 0,
        "url":  base_url + "ArcGIS/rest/services/pat/MapServer"
    }

PAI_DEF = {
        "id":"PAI",
        "title":"PAI",
        "opacity":0.69921875,
        "visibleLayers":[0,1],
        "minScale": 0,
        "maxScale": 0,
        "url":  base_url + "ArcGIS/rest/services/pai/MapServer"
    }

BONIFICA_DEF = {
        "id":"Bonifica",
        "title":"Bonifica",
        "opacity":0.69921875,
        "visibleLayers":[23],
        "minScale": 0,
        "maxScale": 0,
        "url":  base_url + "ArcGIS/rest/services/varie/MapServer"
    }

ORTOFOTO = {
        "id":"Ortofoto",
        "title":"Ortofoto",
        "opacity":1,
        #"visibleLayers":[23],
        "minScale": 0,
        "maxScale": 0,
        "url":  base_url + "ArcGIS/rest/services/foto/MapServer"
    }

AGEA2015 = {
        "id":"Ortofoto",
        "title":"Ortofoto",
        "opacity":1,
        #"visibleLayers":[23],
        "minScale": 0,
        "maxScale": 0,
        "url":  base_url + "ArcGIS/rest/services/agea_2015/MapServer"
    }

DBT2007 = {
        "id":"Db topografico",
        "title":"Db topografico",
        "opacity":1,
        #"visibleLayers":[23],
        "minScale": 0,
        "maxScale": 0,
        "url":  base_url + "ArcGIS/rest/services/dbt/MapServer"
    }

PAT_AUC_DEF = {
        "id":"Db topografico",
        "title":"Db topografico",
        "opacity":1,
        "visibleLayers":[33],
        "minScale": 0,
        "maxScale": 0,
        "url":  "ArcGIS/rest/services/varie/MapServer"
    }

mapExtent_template = '{"xmin":%s,"ymin":%s,"xmax":%s,"ymax":%s,"spatialReference":{"wkid":3003}}'

printOutput_templates = {
    'A4 verticale': {"label": 'A4 Portrait', "size": (210,297)}, 
    'A3 verticale': {"label": 'A3 Portrait', "size": (297,420)}, 
    'A4 orizzontale': {"label": 'A4 Landscape', "size": (297,210)}, 
    'A3 orizzontale': {"label": 'A3 Landscape', "size": (420,297)}, 
}

layoutElements_template = '[{"xOffset":0,"yOffset":0,"symbol":{"text":"%s","textSymbol":{"text":null,"color":{"red":0,"blue":0,"green":0,"alpha":255},"yoffset":0,"font":null,"xoffset":0,"type":"agsJsonSymbol","borderLineColor":null,"angle":0},"type":"pchTextElement"},"visible":true,"width":null,"geometry":{"x":0.6,"y":2.0},"name":"myScaleBar","height":null,"anchor":"topleft"},{"xOffset":0,"yOffset":0,"symbol":{"mapUnitLabel":"","numberFormat":{"roundingValue":3,"roundingOption":0},"pageUnitLabel":"","pageUnits":9,"separator":":","type":"pchScaleText","mapUnits":8,"backgroundColor":{"red":255,"blue":255,"green":255,"alpha":255},"style":0},"visible":true,"width":"","geometry":{"x":0.6,"y":1.5},"name":"myScaleBar","height":"","anchor":"topleft"}]'

proto_ESRI_style = {
        "color": {
            "red": 255,
            "green": 255,
            "blue": 255,
            "alpha": 0
        },
        "style": "esriSFSSolid",
        "type": "esriSFS",
        "outline": {
            "color": {
                "blue": 0,
                "red": 255,
                "green": 0,
                "alpha": 255
            },
            "width": 1.5,
            "style": "esriSLSSolid",
            "type": "esriSLS"
        }
    }

basi = {
    "ctr": [CTR1996_DEF],
    "dbt": [DBT2007],
    "catasto": [CATASTO_DEF],
    "ortofoto 2007": [ORTOFOTO],
    "ortofoto 2015": [AGEA2015],
    "nessuna": [],
}

temi = [
    {
        "label": "pat_vincoli",
        "widget": 4,
        "def": [PAT_VINCOLI_DEF],
        "predef": "true"
    },
    {
        "label": "pat_invarianti",
        "widget": 5,
        "def": [PAT_INVARIANTI_DEF],
        "predef": "false"
    },
    {
        "label": "pat_fragilita",
        "widget": 6,
        "def": [PAT_FRAGILITA_DEF],
        "predef": "false"
    },
    {
        "label": "pat_trasformabilita",
        "widget": 7,
        "def": [PAT_TRASFORMABILITA_DEF],
        "predef": "true"
    },
    {
        "label": "pat_auc",
        "widget": 8,
        "def": [PAT_AUC_DEF],
        "predef": "true"
    },
    {
        "label": "pi_5000",
        "widget": 9,
        "def": [PI_DEF],
        "predef": "true"
    },
    {
        "label": "pi_1000",
        "widget": 10,
        "def": [PI_CS_DEF],
        "predef": "false"
    },
    {
        "label": "altro",
        "widget": 11,
        "def": [BONIFICA_DEF, PAI_DEF],
        "predef": "true"
    },
    {
        "label": "toponomastica",
        "widget": 12,
        "def": [],
        "predef": "false"
    },
]

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


class CDU_GENERA_tool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "CDU_GENERA"
        self.description = "da scrivere"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """
        Define parameter definitions
        https://pro.arcgis.com/en/pro-app/arcpy/geoprocessing_and_python/defining-parameter-data-types-in-a-python-toolbox.htm
        """

        contesto = arcpy.Parameter(
            displayName="Contesto",
            name="contesto",
            datatype="GPFeatureLayer",
            parameterType="Optional",
            direction="Input")

        coordinate_catastali = arcpy.Parameter(
            displayName="Coordinate catastali",
            name="coordinate_catastali",
            datatype="GPString",
            parameterType="Optional",
            direction="Input")

        protocollo_numero = arcpy.Parameter(
            displayName="Protocollo numero",
            name="protocollo_numero",
            datatype="GPString",
            parameterType="Required",
            direction="Input")

        protocollo_data = arcpy.Parameter(
            displayName="Protocollo data",
            name="protocollo_data",
            datatype="GPDate",
            parameterType="Required",
            direction="Input")

        richiedente = arcpy.Parameter(
            displayName="Richiedente",
            name="richiedente",
            datatype="GPString",
            parameterType="Required",
            direction="Input")

        out_odt = arcpy.Parameter(
            displayName="Output certificato",
            name="out_odt",
            datatype="DEFile",
            parameterType="Optional",
            direction="Output")

        params = [contesto, coordinate_catastali, protocollo_numero, protocollo_data, richiedente, out_odt]

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

        default_workspace = "in_memory"
        current_workspace = arcpy.env.scratchWorkspace

        arcpy.ImportToolbox(os.path.join(os.path.dirname(__file__), "URB.pyt"))
        arcpy.gp.toolbox = os.path.join(os.path.dirname(__file__), "URB.pyt")

        # Local variables:
        contesto = parameters[0].valueAsText
        coordinate_catastali = parameters[1].valueAsText
        protocollo_numero = parameters[2].valueAsText
        protocollo_data = parameters[3].valueAsText
        richiedente = parameters[4].valueAsText
        odt_target = parameters[5].valueAsText

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
            PI_def = json.loads(PI_test)
            CS_def = json.loads(CS_test)
            PAT_def = json.loads(PAT_test)
            arcpy.AddMessage(str(PAT_def))
            for item in PAT_def:
                arcpy.AddMessage(item['desc'])
        else:
            poligono = contesto
            identificazione = ""

            if coordinate_catastali:
                CC_result = arcpy.gp.CC2FC_tool(coordinate_catastali)
                arcpy.AddMessage("CC_result: %s" % CC_result.getOutput(0))
                poligono = CC_result.getOutput(0)
                identificazione = u"così individuata nel Catasto Terreni: %s" % decodificaCatasto(coordinate_catastali)
            else:
                if not contesto:
                    arcpy.AddError("Deve essere specificato almeno un contesto, come layer o come coordinate catastali")
                    exit(0)
                poligono = contesto

            # Process: CDU_PI
            PI_result = arcpy.gp.CDU_PI_tool(poligono, output_json)
            arcpy.AddMessage("PI_result: %s" % PI_result.getOutput(1))
            PI_def = json.loads(PI_result.getOutput(1))

            checkInCS = False
            for defin in PI_def:
                if defin["layer"] == 55:
                    checkInCS = True

            if checkInCS:
                # Process: CDU_CS
                CS_result = arcpy.gp.CDU_CS_tool(poligono, output_json)
                arcpy.AddMessage("CS_result: %s" % CS_result.getOutput(1))
                CS_def = json.loads(CS_result.getOutput(1))
            else:
                CS_def = []

            # Process: CDU_PAT
            PAT_result = arcpy.gp.CDU_PAT_tool(poligono, output_json__2_)
            arcpy.AddMessage("PAT_result: %s" % PAT_result.getOutput(1))
            PAT_def = json.loads(PAT_result.getOutput(1))

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

        parameters[5].value = odt_target


class INQUA_tool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "CDU_INQUA"
        self.description = "da scrivere"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """
        Define parameter definitions
        https://pro.arcgis.com/en/pro-app/arcpy/geoprocessing_and_python/defining-parameter-data-types-in-a-python-toolbox.htm
        """

        contesto = arcpy.Parameter(
            displayName="Contesto",
            name="contesto",
            datatype="GPFeatureLayer",
            parameterType="Optional",
            direction="Input")

        coordinate_catastali = arcpy.Parameter(
            displayName="Coordinate catastali",
            name="coordinate_catastali",
            datatype="GPString",
            parameterType="Optional",
            direction="Input")

        formato = arcpy.Parameter(
            displayName="Protocollo numero",
            name="protocollo_numero",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        formato.filter.type = "ValueList"
        formato.filter.list = [
            "A4 verticale",
            "A4 orizzontale",
            "A3 verticale",
            "A3 orizzontale",
        ]
        formato.value = "A4 verticale"

        base_cartografica = arcpy.Parameter(
            displayName="Base cartografica",
            name="base_cartografica",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        base_cartografica.filter.type = "ValueList"
        base_cartografica.filter.list = [
            "ctr",
            "dbt",
            "catasto",
            "ortofoto 2007",
            "ortofoto 2015",
            "nessuna",
        ]
        base_cartografica.value = "ctr"

        out_pdf = arcpy.Parameter(
            displayName="Output inquadramento",
            name="out_pdf",
            datatype="DEFile",
            parameterType="Optional",
            direction="Output")


        temi_params = []
        for tema in temi:
            tema_widget = arcpy.Parameter(
                    displayName=tema["label"].replace("_", " "),
                    name=tema["label"],
                    datatype="GPBoolean",
                    parameterType="Required",
                    direction="Output")
            tema_widget.value = tema["predef"]
            temi_params.append(tema_widget)
                

        params = [contesto, coordinate_catastali, formato, base_cartografica] + temi_params + [out_pdf]

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

        default_workspace = "in_memory"
        current_workspace = arcpy.env.scratchWorkspace

        arcpy.ImportToolbox(os.path.join(os.path.dirname(__file__), "URB.pyt"))
        arcpy.gp.toolbox = os.path.join(os.path.dirname(__file__), "URB.pyt")

        def extentToPoly(extent, srid=3003):
            clist = arcpy.Array()
            clist.append(arcpy.Point(extent.XMin, extent.YMin))
            clist.append(arcpy.Point(extent.XMin, extent.YMax))
            clist.append(arcpy.Point(extent.XMax, extent.YMax))
            clist.append(arcpy.Point(extent.XMax, extent.YMin))
            return  arcpy.Polygon(clist)

        def get_best_fit_scale(fc,paper,scales=[1000,2000,2500,5000,7500,10000,20000]):
            desc = arcpy.Describe(fc)
            sheet = printOutput_templates[paper]["size"]
            margin = 10
            #mapUnitsPerMillimeter = [0.5,1,2,5,10]
            cx = (desc.extent.XMin + desc.extent.XMax)/2
            cy = (desc.extent.YMin + desc.extent.YMax)/2
            fc_bound = extentToPoly(desc.extent)

            for scale in scales:
                scaleFactor = scale / 1000
                wb = sheet[0] * scaleFactor / 2
                hb = sheet[1] * scaleFactor / 2
                wf = (sheet[0] - margin*2) * scaleFactor / 2
                hf = (sheet[1] - margin*2) * scaleFactor / 2
                
                #bound = arcpy.Polygon([arcpy.Point(cx-wb,cy-hb), arcpy.Point(cx+wb,cy-hb), arcpy.Point(cx+wb,cy+hb), arcpy.Point(cx-wb,cy+hb)])
                #frame = arcpy.Polygon([arcpy.Point(cx-wf,cy-hf), arcpy.Point(cx+wf,cy-hf), arcpy.Point(cx+wf,cy+hf), arcpy.Point(cx-wf,cy+hf)])
                bound = extentToPoly(arcpy.Extent(cx-wb, cy-hb, cx+wb, cy+hb))
                frame_extent = arcpy.Extent(cx-wf, cy-hf, cx+wf, cy+hf)
                frame = extentToPoly(frame_extent)

                #tempfcname = "in_memory/output" + uuid.uuid4().hex
                #arcpy.Intersect_analysis ([frame, fc_bound], tempfcname)
                #result = arcpy.GetCount_management(tempfcname)
                #intersections = int(result.getOutput(0))

                #if intersections > 0:
                if frame_extent.contains(desc.extent):
                    return bound, frame, scale

            return bound, frame, scaleFactor

        def get_esri_ring(extent):
            ring = [
                [extent.XMin, extent.YMin],
                [extent.XMax, extent.YMin],
                [extent.XMax, extent.YMax],
                [extent.XMin, extent.YMax],
                [extent.XMin, extent.YMin],
            ]
            return ring

        probe_path = parameters[0].valueAsText
        coordinate_catastali = parameters[1].valueAsText
        paper = parameters[2].valueAsText.replace("'","")
        base = parameters[3].valueAsText.replace("'","")

        checkboxes = []
        #for idx in range(4,12):
        #    if parameters[idx].valueAsText == "true":
        #        checkboxes.append(idx)
        for param in parameters:
            #arcpy.AddMessage("param: %s %s" % (str(param.datatype),str(param.valueAsText)))
            if param.datatype == "Booleano" and param.valueAsText == "true":
                checkboxes.append(param.name)
        arcpy.AddMessage("checkboxes: %s" % str(checkboxes))

        with open(os.path.join(os.path.dirname(__file__),"web_map_as_json.json"),"r") as jf:
            wmaj_template = jf.read()

        template_engine = Template(wmaj_template)

        decode_map = []

        if coordinate_catastali:
            CC_result = arcpy.gp.coordinateCatastaliToLayer(coordinate_catastali)
            probe_path = CC_result.getOutput(0)
        else:
            if not probe_path:
                arcpy.AddError("Deve essere specificata almeno un contesto, come layer o come coordinate catastali")
                exit(0)
            
        arcpy.AddMessage("probe_path: %s paper:" % probe_path)
        probe = arcpy.mapping.Layer(probe_path)
        with arcpy.da.SearchCursor(probe_path, ['SHAPE']) as cursor:  
            probe_polygon = next(cursor)[0]

        probe_json_path = os.path.join(tempfile.mkdtemp(), "probe.json")
        arcpy.FeaturesToJSON_conversion(probe_path, probe_json_path, "FORMATTED")

        with open(probe_json_path ,"r") as jf:
            probe_json = jf.read()

        #arcpy.AddMessage(json.dumps(json.loads(probe_json),indent=3))

        json_feats = []
        probe_json_dict = json.loads(probe_json)
        for feat in probe_json_dict["features"]:
            feat["symbol"] = {
                "color": [255, 0, 0, 0],
                "outline": {
                    "color": [255, 0, 0, 255],
                    "width": 1.75,
                    "type": "esriSLS",
                    "style": "esriSLSSolid"
                },
                "type": "esriSFS",
                "style": "esriSFSSolid"
            }
            json_feats.append(feat)


        result_pdf = []

        for tema in temi:
            if not tema["label"] in checkboxes:
                continue
            
            mapServices = basi[base] + tema["def"]

            bound, frame, scale = get_best_fit_scale(probe_path, paper)

            printpar ={
                "extent": [ frame.extent.XMin, frame.extent.YMin, frame.extent.XMax, frame.extent.YMax ],
                "scale": scale,
                "srid": 3003,
                "esri_poly": json.dumps(json.loads(probe_json)["features"][0]["geometry"]["rings"]),
                "esri_style": json.dumps(proto_ESRI_style), #non implementato nel template json
                "esri_bound": get_esri_ring(bound.extent),
                "esri_frame": get_esri_ring(frame.extent),
                "title": tema["label"].upper().replace("_",""),
                "dpi": 200,
                "auth": "Settore urbanistica, Servizi catastali e Mobilita'",
                "copyright": "Comune di Padova"
            }

            web_map_as_json = template_engine.render(printpar = printpar)
            web_map_as_dict = json.loads(web_map_as_json)

            web_map_as_dict["operationalLayers"][0]["featureCollection"]["layers"][0]["featureSet"]["features"] = json_feats
            web_map_as_dict["operationalLayers"] = mapServices + web_map_as_dict["operationalLayers"]
            web_map_as_json = json.dumps(web_map_as_dict)

            post_parameters = {
                "f": "json",
                "Web_Map_as_JSON": web_map_as_json,
                "Format": "PDF",
                "Layout_Template": printOutput_templates[paper]["label"]
            }

            #arcpy.AddMessage(json.dumps(post_parameters,indent=3))

            pdf_file_path = os.path.join(tempfile.mkdtemp(), tema["label"]+".pdf")

            res = urllib.urlopen(base_url + "arcgis/rest/services/Utilities/PrintingTools/GPServer/Export%20Web%20Map%20Task/execute", urllib.urlencode(post_parameters)).read()

            if  "results" in res:
                remoteFile = json.loads(res)['results'][0]["value"]["url"]
                #arcpy.AddMessage ("REMOTE: " + remoteFile)
                urllib.urlretrieve(remoteFile, pdf_file_path)
                arcpy.AddMessage("OK: %s" % tema["label"])
                result_pdf.append(pdf_file_path)
            else:
                arcpy.AddMessage("NO")

        if parameters[-1].valueAsText:
            pdf_globale = parameters[-1].valueAsText
        else:
            pdf_globale = os.path.join(tempfile.mkdtemp(), "inquadramento.pdf")

        merger = PdfFileMerger()
        for file in result_pdf:
            merger.append(PdfFileReader(file))
        merger.write(pdf_globale)

        parameters[-1].value = pdf_globale

        arcpy.AddMessage("OK: %s" % pdf_globale)