# -*- coding: utf-8 -*-
from Autodesk.Revit.DB import *
from pyrevit import revit, DB, forms

doc = revit.doc
app = revit.doc.Application

PARAM_NAMES = [
    "Location", "Tag", "Wall opening dim.", "Type", "Quantity", "Open area", 
    "Frame size", "Frame material", "Frame finish", "Door panel material", 
    "Door panel finish", "Window panel material", "Window panel finish", "Internal panel type", "Fire rating", "Acoustic rating", 
    "Hinges/sliding gear", "Handle", "Lock set", "Door viewer", "Door closer", 
    "Soft closing", "Flush bolts", "Door stopper", "Rubber seal", "Kick plate", "Access control", "SheetNumber",
    "ShadingCanopy"
]
GROUP_NAME = "RYN_Schedule"
PREFIX = "RYN_Schedule_"

def show_alert(msg):
    forms.alert(msg, exitscript=False)

def get_or_create_shared_params():
    spf = app.OpenSharedParameterFile()
    if not spf: return None, "No shared parameter file loaded in Revit!"
    
    group = spf.Groups.get_Item(GROUP_NAME)
    if not group:
        try:
            group = spf.Groups.Create(GROUP_NAME)
        except Exception as e:
            return None, "Failed to create group in Shared Parameter File: " + str(e)
            
    param_defs = []
    for name in PARAM_NAMES:
        full_name = PREFIX + name
        p_def = group.Definitions.get_Item(full_name)
        if not p_def:
            try:
                # Revit 2022+ 
                opt = ExternalDefinitionCreationOptions(full_name, SpecTypeId.String.Text)
                p_def = group.Definitions.Create(opt)
            except:
                try:
                    # Revit < 2022
                    opt = ExternalDefinitionCreationOptions(full_name, ParameterType.Text)
                    p_def = group.Definitions.Create(opt)
                except Exception as e:
                    pass
                    
        if p_def: 
            param_defs.append(p_def)
            
    return param_defs, "Found/Created {} defs in SPF".format(len(param_defs))

def load_into_family(param_defs):
    fmr = doc.FamilyManager
    existing_params = [p.Definition.Name for p in fmr.Parameters]
    added = 0
    with DB.Transaction(doc, "Add Shared Parameters") as t:
        t.Start()
        for p_def in param_defs:
            if p_def.Name not in existing_params:
                try:
                    fmr.AddParameter(p_def, GroupTypeId.Data, True)
                    added += 1
                except: pass
        t.Commit()
    show_alert("Successfully added {} new Instance Parameters to the Family!".format(added))

def load_into_project(param_defs):
    cats = app.Create.NewCategorySet()
    cats.Insert(doc.Settings.Categories.get_Item(BuiltInCategory.OST_Doors))
    cats.Insert(doc.Settings.Categories.get_Item(BuiltInCategory.OST_Windows))
    binding = app.Create.NewInstanceBinding(cats)
    
    iterator = doc.ParameterBindings.ForwardIterator()
    existing_bound_names = []
    while iterator.MoveNext():
        existing_bound_names.append(iterator.Key.Name)
        
    added = 0
    errors = []
    with DB.Transaction(doc, "Add Project Parameters") as t:
        t.Start()
        for p_def in param_defs:
            if p_def.Name in existing_bound_names:
                errors.append(p_def.Name + " (Already bound)")
                continue
            try:
                success = doc.ParameterBindings.Insert(p_def, binding, GroupTypeId.Data)
                if success:
                    added += 1
                else:
                    errors.append(p_def.Name + " (Insert False)")
            except Exception as e:
                errors.append(p_def.Name + " (Exception: " + str(e) + ")")
        t.Commit()
        
    msg = "Successfully added: {}\n\nErrors / Skipped:\n{}".format(added, "\n".join(errors))
    show_alert(msg)

def main():
    if not doc: return
    param_defs, msg = get_or_create_shared_params()
    if not param_defs:
        show_alert(msg)
        return
        
    if doc.IsFamilyDocument:
        load_into_family(param_defs)
    else:
        load_into_project(param_defs)

if __name__ == '__main__':
    main()
