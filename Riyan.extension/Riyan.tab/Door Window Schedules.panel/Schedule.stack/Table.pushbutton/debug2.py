import clr
clr.AddReference('RevitAPI')
import Autodesk.Revit.DB as DB

import sys

props = [p for p in dir(DB.ViewSheet) if 'collection' in p.lower()]
with open('C:\\Users\\User\\Desktop\\TEST\\sheet_collection_test.txt', 'w') as f:
    f.write(str(props))
