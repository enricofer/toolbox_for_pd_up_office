
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

from PyPDF2 import PdfFileMerger, PdfFileReader


from jinja2 import Template

base_url = 'http://10.10.20.58/'

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


CTR1996_DEF = {
        "id":"Ctr 1996",
        "title":"Ctr 1996",
        "opacity":0.69921875,
        #"visibleLayers":[0,2,3,4,5,6,7,8,10,11,13],
        "minScale": 0,
        "maxScale": 0,
        "url":  "http://10.10.20.58/ArcGIS/rest/services/CTR_PRG/MapServer/"
    }

CATASTO_DEF = {
        "id":"Catasto",
        "title":"Catasto",
        "opacity":0.69921875,
        "visibleLayers":[4,6,7],
        "minScale": 0,
        "maxScale": 0,
        "url":  "http://10.10.20.58/ArcGIS/rest/services/catasto/MapServer/"
    }

PI_DEF = {
        "id":"Ctr 1996",
        "title":"Ctr 1996",
        "opacity":0.69921875,
        #"visibleLayers":[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18],
        "visibleLayers":[0,1,2,3,4],
        "minScale": 0,
        "maxScale": 0,
        "url":  "http://10.10.20.58/ArcGIS/rest/services/prg/MapServer"
    }

TOPO_DEF = {
        "id":"Topo",
        "title":"Topo",
        "opacity":0.69921875,
        "visibleLayers":[0],
        "minScale": 0,
        "maxScale": 0,
        "url":  "http://10.10.20.58/ArcGIS/rest/services/base/MapServer"
    }

PI_CS_DEF = {
        "id":"PI Centro Storico",
        "title":"PI Centro Storico",
        "opacity":0.69921875,
        "visibleLayers":[3,4,6,7,9,10,11,12,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30],
        "minScale": 0,
        "maxScale": 0,
        "url":  "http://10.10.20.58/ArcGIS/rest/services/pr1000/MapServer"
    }

PAT_TRASFORMABILITA_DEF = {
        "id":"Pat trasformabilita",
        "title":"Pat trasformabilita",
        "opacity":0.69921875,
        "visibleLayers":[36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68],
        "minScale": 0,
        "maxScale": 0,
        "url":  "http://10.10.20.58/ArcGIS/rest/services/pat/MapServer"
    }

PAT_VINCOLI_DEF = {
        "id":"Pat vincoli",
        "title":"Pat vincoli",
        "opacity":0.69921875,
        "visibleLayers":[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19],
        "minScale": 0,
        "maxScale": 0,
        "url":  "http://10.10.20.58/ArcGIS/rest/services/pat/MapServer"
    }

PAT_FRAGILITA_DEF = {
        "id":"Pat fragilita",
        "title":"Pat fragilita",
        "opacity":0.69921875,
        "visibleLayers":[30,31,32,33,34],
        "minScale": 0,
        "maxScale": 0,
        "url":  "http://10.10.20.58/ArcGIS/rest/services/pat/MapServer"
    }

PAT_INVARIANTI_DEF = {
        "id":"Pat fragilita",
        "title":"Pat fragilita",
        "opacity":0.69921875,
        "visibleLayers":[21,22,23,24,25,26,27,28],
        "minScale": 0,
        "maxScale": 0,
        "url":  "http://10.10.20.58/ArcGIS/rest/services/pat/MapServer"
    }

PAI_DEF = {
        "id":"PAI",
        "title":"PAI",
        "opacity":0.69921875,
        "visibleLayers":[0,1],
        "minScale": 0,
        "maxScale": 0,
        "url":  "http://10.10.20.58/ArcGIS/rest/services/pai/MapServer"
    }

BONIFICA_DEF = {
        "id":"Bonifica",
        "title":"Bonifica",
        "opacity":0.69921875,
        "visibleLayers":[23],
        "minScale": 0,
        "maxScale": 0,
        "url":  "http://10.10.20.58/ArcGIS/rest/services/varie/MapServer"
    }

ORTOFOTO = {
        "id":"Ortofoto",
        "title":"Ortofoto",
        "opacity":1,
        #"visibleLayers":[23],
        "minScale": 0,
        "maxScale": 0,
        "url":  "http://10.10.20.58/ArcGIS/rest/services/foto/MapServer"
    }

AGEA2015 = {
        "id":"Ortofoto",
        "title":"Ortofoto",
        "opacity":1,
        #"visibleLayers":[23],
        "minScale": 0,
        "maxScale": 0,
        "url":  "http://10.10.20.58/ArcGIS/rest/services/agea_2015/MapServer"
    }

DBT2007 = {
        "id":"Db topografico",
        "title":"Db topografico",
        "opacity":1,
        #"visibleLayers":[23],
        "minScale": 0,
        "maxScale": 0,
        "url":  "http://10.10.20.58/ArcGIS/rest/services/dbt/MapServer"
    }

PAT_AUC_DEF = {
        "id":"Db topografico",
        "title":"Db topografico",
        "opacity":1,
        "visibleLayers":[33],
        "minScale": 0,
        "maxScale": 0,
        "url":  "http://pataplan/ArcGIS/rest/services/varie/MapServer"
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
        "def": [PAT_VINCOLI_DEF]
    },
    {
        "label": "pat_invarianti",
        "widget": 5,
        "def": [PAT_INVARIANTI_DEF]
    },
    {
        "label": "pat_fragilita",
        "widget": 6,
        "def": [PAT_FRAGILITA_DEF]
    },
    {
        "label": "pat_trasformabilita",
        "widget": 7,
        "def": [PAT_TRASFORMABILITA_DEF]
    },
    {
        "label": "pat_auc",
        "widget": 8,
        "def": [PAT_AUC_DEF]
    },
    {
        "label": "pi_5000",
        "widget": 9,
        "def": [PI_DEF]
    },
    {
        "label": "pi_1000",
        "widget": 10,
        "def": [PI_CS_DEF]
    },
    {
        "label": "altro",
        "widget": 11,
        "def": [BONIFICA_DEF, PAI_DEF]
    },
    {
        "label": "toponomastica",
        "widget": 12,
        "def": []
    },
]

probe_path = arcpy.GetParameterAsText(0)
coordinate_catastali = arcpy.GetParameterAsText(1)
paper = arcpy.GetParameterAsText(2).replace("'","")
base = arcpy.GetParameterAsText(3).replace("'","")

checkboxes = []
for idx in range(4,12):
    if arcpy.GetParameterAsText(idx) == "true":
        checkboxes.append(idx)
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
    if not tema["widget"] in checkboxes:
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

if arcpy.GetParameterAsText(14):
    pdf_globale = arcpy.GetParameterAsText(14)
else:
    pdf_globale = os.path.join(tempfile.mkdtemp(), "inquadramento.pdf")

merger = PdfFileMerger()
for file in result_pdf:
    merger.append(PdfFileReader(file))
merger.write(pdf_globale)

arcpy.SetParameter(14,pdf_globale)

arcpy.AddMessage("OK: %s" % pdf_globale)


