# -*- coding: utf-8 -*-
from pyrevit import revit, DB, forms

doc = revit.doc

def get_location(el):
    if el.Location and isinstance(el.Location, DB.LocationPoint):
        return el.Location.Point
    bb = el.get_BoundingBox(doc.ActiveView) if doc.ActiveView else el.get_BoundingBox(None)
    if bb:
        return (bb.Min + bb.Max) / 2.0
    return DB.XYZ.Zero

def get_prefix(el_type, base_prefix):
    name = el_type.FamilyName.upper() + " " + (el_type.Name.upper() if hasattr(el_type, "Name") else "")
    if "OPN" in name: return "OP"
    if "ARCHITRAVE" in name: return "A"
    return base_prefix

def process_elements():
    doors = DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Doors).WhereElementIsNotElementType().ToElements()
    windows = DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Windows).WhereElementIsNotElementType().ToElements()
    
    unique_types = {}
    
    # Process all elements
    for el in list(doors) + list(windows):
        loc = get_location(el)
        t_id = el.GetTypeId()
        if t_id != DB.ElementId.InvalidElementId:
            if t_id not in unique_types:
                unique_types[t_id] = {'el': el, 'loc': loc, 'type': doc.GetElement(t_id), 'cat': el.Category.Id.IntegerValue}
            else:
                existing_loc = unique_types[t_id]['loc']
                if loc.Z > existing_loc.Z + 0.1 or (abs(loc.Z - existing_loc.Z) <= 0.1 and loc.X < existing_loc.X):
                    unique_types[t_id]['loc'] = loc
                    
    def sort_key(item):
        # Group by floor level (approx 10 feet) to avoid sill height messing up the X sort
        z_group = round(item['loc'].Z / 10.0)
        return (-z_group, item['loc'].X)
        
    items = list(unique_types.values())
    items.sort(key=sort_key)
    
    counters = {"D": 1, "W": 1, "OP": 1, "A": 1}
    
    for item in items:
        el_type = item['type']
        base_pref = "D" if item['cat'] == int(DB.BuiltInCategory.OST_Doors) else "W"
        pref = get_prefix(el_type, base_pref)
        
        p = el_type.get_Parameter(DB.BuiltInParameter.ALL_MODEL_TYPE_MARK)
        if p and not p.IsReadOnly:
            p.Set("{}{}".format(pref, counters[pref]))
            counters[pref] += 1
            
    return counters

def main():
    with DB.Transaction(doc, "Auto Renumber Tags") as t:
        t.Start()
        counters = process_elements()
        t.Commit()
        
    msg = "Successfully renumbered:\n"
    if counters["D"] > 1: msg += "- {} Doors (D1, D2...)\n".format(counters["D"] - 1)
    if counters["W"] > 1: msg += "- {} Windows (W1, W2...)\n".format(counters["W"] - 1)
    if counters["OP"] > 1: msg += "- {} Openings (OP1, OP2...)\n".format(counters["OP"] - 1)
    if counters["A"] > 1: msg += "- {} Architraves (A1, A2...)\n".format(counters["A"] - 1)
    
    forms.alert(msg)

if __name__ == "__main__":
    main()
