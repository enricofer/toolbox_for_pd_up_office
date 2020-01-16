

# -*- coding: utf-8 -*-

#---------------------------------------------------------------------
# Name:        toolbox per la generazione di CDU - Comune di Padova
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

#from ZTO import ZTO2006Tool, ZTOSCVOLTool
#from ANALISI import CDUPItool, CDUPATtool, CDUCStool, CC2FCtool
#from EXPORT import CDUGENERAtool, INQUAtool

import ZTO
import ANALISI
import EXPORT
reload(ZTO)
reload(ANALISI)
reload(EXPORT)
ZTO2006Tool = ZTO.ZTO2006Tool
ZTOSCVOLTool = ZTO.ZTOSCVOLTool
CDUPItool = ANALISI.CDUPItool
CDUPATtool = ANALISI.CDUPATtool
CDUCStool = ANALISI.CDUCStool
CC2FCtool = ANALISI.CC2FCtool
CDUGENERAtool = EXPORT.CDUGENERAtool
INQUAtool = EXPORT.INQUAtool

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = " URB Toolbox"
        self.alias = ""

        # List of tool classes associated with this toolbox
        self.tools = [ZTO2006Tool, ZTOSCVOLTool, CDUPItool, CDUPATtool, CDUCStool, CC2FCtool, CDUGENERAtool, INQUAtool]
