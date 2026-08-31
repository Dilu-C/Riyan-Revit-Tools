# -*- coding: utf-8 -*-
from Autodesk.Revit.DB import *
from pyrevit import revit, DB, forms

doc = revit.doc
app = revit.doc.Application

def main():
    if not doc: return
    
    removed = 0
    with DB.Transaction(doc, "Remove Old Parameters") as t:
        t.Start()
        
        if doc.IsFamilyDocument:
            # Remove from Family
            fmr = doc.FamilyManager
            to_remove = []
            for p in fmr.Parameters:
                if p.Definition.Name.startswith("RYN_Door_Schedule_"):
                    to_remove.append(p)
                    
            if not to_remove:
                forms.alert("No old 'RYN_Door_Schedule_' parameters found in this Family.")
                t.RollBack()
                return
                
            for p in to_remove:
                try:
                    fmr.RemoveParameter(p)
                    removed += 1
                except: pass
        else:
            # Remove from Project
            iterator = doc.ParameterBindings.ForwardIterator()
            to_remove = []
            while iterator.MoveNext():
                p_def = iterator.Key
                if p_def.Name.startswith("RYN_Door_Schedule_"):
                    to_remove.append(p_def)
                    
            if not to_remove:
                forms.alert("No old 'RYN_Door_Schedule_' parameters found in the Project.")
                t.RollBack()
                return
                
            for p_def in to_remove:
                try:
                    doc.ParameterBindings.Remove(p_def)
                    removed += 1
                except: pass
                
        t.Commit()
        
    forms.alert("Successfully removed {} old 'RYN_Door_Schedule_' parameters!".format(removed))

if __name__ == '__main__':
    main()