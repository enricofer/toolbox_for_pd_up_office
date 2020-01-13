
import arcpy

from ZTO import ZTO_2006_Tool, ZTO_SC_VOL_Tool
from ANALISI import CDU_PI_tool, CDU_PAT_tool, CDU_CS_tool, CC2FC_tool
from EXPORT import CDU_GENERA_tool, INQUA_tool

import ZTO
import ANALISI
import EXPORT
reload(ZTO)
reload(ANALISI)
reload(EXPORT)
ZTO_2006_Tool = ZTO.ZTO_2006_Tool
ZTO_SC_VOL_Tool = ZTO.ZTO_SC_VOL_Tool
CDU_PI_tool = ANALISI.CDU_PI_tool
CDU_PAT_tool = ANALISI.CDU_PAT_tool
CDU_CS_tool = ANALISI.CDU_CS_tool
CC2FC_tool = ANALISI.CC2FC_tool
CDU_GENERA_tool = EXPORT.CDU_GENERA_tool
INQUA_tool = EXPORT.INQUA_tool

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = " URB Toolbox"
        self.alias = ""

        # List of tool classes associated with this toolbox
        self.tools = [ZTO_2006_Tool, ZTO_SC_VOL_Tool, CDU_PI_tool, CDU_PAT_tool, CDU_CS_tool, CC2FC_tool, CDU_GENERA_tool, INQUA_tool]
