import clr
clr.AddReference('RevitAPI')
import Autodesk.Revit.DB as DB
def execute(doc):
    with open('C:\\Users\\User\\Desktop\\TEST\\sheet_test.txt', 'w') as f:
        f.write(str(hasattr(DB.Viewport, 'GetLabelOutline')))
