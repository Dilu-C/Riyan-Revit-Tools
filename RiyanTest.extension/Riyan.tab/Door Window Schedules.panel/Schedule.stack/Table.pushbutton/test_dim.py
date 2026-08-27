import clr
clr.AddReference("RevitAPI")
clr.AddReference("RevitServices")
from Autodesk.Revit.DB import *
from pyrevit import revit, script

doc = revit.doc
view = doc.ActiveView

with revit.Transaction("Test Dim"):
    p1 = XYZ(0, 0, 0)
    p2 = XYZ(10, 0, 0)
    
    line1 = Line.CreateBound(p1 + XYZ(0, 1, 0), p1 - XYZ(0, 1, 0))
    line2 = Line.CreateBound(p2 + XYZ(0, 1, 0), p2 - XYZ(0, 1, 0))
    
    dc1 = doc.Create.NewDetailCurve(view, line1)
    dc2 = doc.Create.NewDetailCurve(view, line2)
    
    doc.Regenerate()
    
    ref_arr = ReferenceArray()
    ref_arr.Append(dc1.GeometryCurve.Reference)
    ref_arr.Append(dc2.GeometryCurve.Reference)
    
    dim_line = Line.CreateBound(p1 + XYZ(0, -2, 0), p2 + XYZ(0, -2, 0))
    dim = doc.Create.NewDimension(view, dim_line, ref_arr)
    dim.Below = "TEST DIM"
    
    print("Created dim: " + str(dim.Id))
