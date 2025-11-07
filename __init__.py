# -------------------------------------------------------------------------------
# Point Importer Package Initialization
#
# This package provides CSV point import and export tools for Visual Components:
# 1. CSV Point Import - Import 3D points or joint angles from CSV files into robot routines
# 2. CSV Point Export - Export 3D points or joint angles from robot routines to CSV files
# 3. Test Script - Utility script for testing robot program statements
#
# Usage:
# - Import Points: Load CSV files with X,Y,Z[,W,P,R] or joint angles into robot routines
# - Export Points: Export robot routine points to CSV files in various formats
# - Test Script: Debug and inspect robot program statements
#
# All commands are added to the VcTabTeach/Beck menu and Tools menu in Visual Components.
# -------------------------------------------------------------------------------

from vcApplication import *


def OnStart():
    """
    Initialize the Point Importer package.

    Loads all point import/export commands and adds them to the Visual Components
    menu system under VcTabTeach/Beck and Tools menu.

    Commands loaded:
    - importPointsCSV: Import 3D points or joint angles from CSV files
    - exportPointsCSV: Export 3D points or joint angles to CSV files
    - testScript: Test utility for robot program statements
    """

    # Load CSV Point Import command
    cmduri = getApplicationPath() + "importPointsCSV.py"
    cmd = loadCommand("importPointsCSV", cmduri)
    addMenuItem("VcTabTeach/Beck", "Import Points", -1, "importPointsCSV")
    # Also add to main menu bar (top level Tools menu)
    addMenuItem("Tools", "Import Points CSV", -1, "importPointsCSV")

    # Load CSV Point Export command
    cmduri = getApplicationPath() + "exportPointsCSV.py"
    cmd = loadCommand("exportPointsCSV", cmduri)
    addMenuItem("VcTabTeach/Beck", "Export Points", -1, "exportPointsCSV")
    # Also add to main menu bar (top level Tools menu)
    addMenuItem("Tools", "Export Points CSV", -1, "exportPointsCSV")

    # Load Test Script command
    cmduri = getApplicationPath() + "testScript.py"
    cmd = loadCommand("testScript", cmduri)
    addMenuItem("VcTabTeach/Beck", "Test Script", -1, "testScript")
    # Also add to main menu bar (top level Tools menu)
    addMenuItem("Tools", "Test Script", -1, "testScript")
