# -*- coding: utf-8 -*-
from Autodesk.Revit.DB import *
from pyrevit import revit, DB
from Autodesk.Revit.UI import TaskDialog

doc = revit.doc
uidoc = revit.uidoc

def main():
    if not doc.IsFamilyDocument:
        TaskDialog.Show("Error", "This tool must be run inside the Family Editor!")
        return
        
    sel_ids = uidoc.Selection.GetElementIds()
    if not sel_ids:
        TaskDialog.Show("Error", "Please select the '?' generic annotations first!")
        return
        
    elements = [doc.GetElement(eid) for eid in sel_ids]
    
    potential_titles = []
    
    def get_element_text(element):
        if hasattr(element, "Text"): return element.Text
        for p_name in ["TextValue", "Label", "Text", "Title", "Text Value"]:
            p = element.LookupParameter(p_name)
            if p and p.HasValue:
                v = p.AsString()
                if v: return v
        return None
        
    for tn in DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_TextNotes).WhereElementIsNotElementType():
        txt = get_element_text(tn)
        if txt and txt.strip() != "?" and txt.strip() != "":
            potential_titles.append((tn, txt))
            
    for ga in DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_GenericAnnotation).WhereElementIsNotElementType():
        if ga.Id in sel_ids: continue
        txt = get_element_text(ga)
        if txt and txt.strip() != "?" and txt.strip() != "":
            potential_titles.append((ga, txt))
    
    fmr = doc.FamilyManager
    family_params = {p.Definition.Name: p for p in fmr.Parameters}
    
    # Check if this is a window schedule by reading the text on the sheet!
    is_window_schedule = False
    for el, txt in potential_titles:
        if "WINDOW PANEL" in txt.upper():
            is_window_schedule = True
            break
            
    mapping_rules = {
        "LOCATION": "Location",
        "TAG": "Tag",
        "WALL OPENING DIM.": "Wall opening dim.",
        "TYPE": "Type",
        "QUANTITY": "Quantity",
        "OPEN AREA": "Open area",
        "FRAME SIZE": "Frame size",
        "MATERIAL": ["Frame material", "Window panel finish" if is_window_schedule else "Door panel material"],
        "FINISH": ["Frame finish", "Window panel finish" if is_window_schedule else "Door panel finish"],
        "INTERNAL PANEL TYPE": "Internal panel type",
        "FIRE RATING": "Fire rating",
        "ACOUSTIC RATING": "Acoustic rating",
        "HINGES/ SLIDING GEAR": "Hinges/sliding gear",
        "HINGES/SLIDING GEAR": "Hinges/sliding gear",
        "HANDLE": "Handle",
        "LOCK SET": "Lock set",
        "DOOR VIEWER": "Door viewer",
        "DOOR CLOSER": "Door closer",
        "SOFT CLOSING": "Soft closing",
        "FLUSH BOLTS": "Flush bolts",
        "DOOR STOPPER": "Door stopper",
        "RUBBER SEAL": "Rubber seal",
        "KICK PLATE": "Kick plate",
        "ACCESS CONTROL": "Access control",
        "SHADING CANOPY": "ShadingCanopy"
    }
    
    current_view = doc.ActiveView
    
    # Sort descending by Y
    elements.sort(key=lambda el: -el.get_BoundingBox(current_view).Min.Y if el.get_BoundingBox(current_view) else 0)
    
    mapped_count = 0
    errors = []
    
    with DB.Transaction(doc, "Map Parameters Fast") as t:
        t.Start()
        for el in elements:
            bbox = el.get_BoundingBox(current_view)
            if not bbox: continue
            q_y = (bbox.Min.Y + bbox.Max.Y) / 2.0
            q_x = bbox.Min.X
            
            closest_text = None
            min_dist = 999999
            
            for title_el, title_txt in potential_titles:
                tn_bbox = title_el.get_BoundingBox(current_view)
                if not tn_bbox: continue
                t_y = (tn_bbox.Min.Y + tn_bbox.Max.Y) / 2.0
                
                # Check center Y difference
                if abs(t_y - q_y) < 0.2: 
                    # Must start to the left
                    if tn_bbox.Min.X < q_x + 0.1: 
                        dist = abs(q_x - tn_bbox.Max.X)
                        if dist < min_dist:
                            min_dist = dist
                            closest_text = title_txt.strip().upper()
                            
            if not closest_text:
                errors.append("Skipped ? at Y={:.2f} (No text found to its left)".format(q_y))
                continue
                
            matched_key = None
            for key in mapping_rules.keys():
                if closest_text == key or closest_text.replace(" ", "") == key.replace(" ", ""):
                    matched_key = key
                    break
                    
            if not matched_key:
                errors.append("Unrecognized title text: '{}'".format(closest_text))
                continue
                
            val = mapping_rules[matched_key]
            if isinstance(val, list):
                if len(val) > 0:
                    param_suffix = val.pop(0)
                else:
                    errors.append("Skipped '{}' (Too many ? marks selected for this title)".format(matched_key))
                    continue
            else:
                param_suffix = val
                
            p_name = "RYN_Schedule_" + param_suffix
            
            # Find the text parameter - search for Text, Label, Value without IsReadOnly check
            text_val_param = el.LookupParameter("TextValue")
            if not text_val_param:
                for p in el.Parameters:
                    if p.Definition.Name in ["Text", "Label", "Value"]:
                        if p.StorageType == StorageType.String:
                            text_val_param = p
                            break
                        
            if not text_val_param:
                errors.append("Failed to find TextValue parameter on ? mark")
                continue
                
            if p_name in family_params:
                try:
                    # Overwrite directly
                    fmr.AssociateElementParameterToFamilyParameter(text_val_param, family_params[p_name])
                    mapped_count += 1
                except Exception as e:
                    errors.append("Error mapping '{}': {}".format(p_name, str(e)))
            else:
                errors.append("Parameter '{}' does not exist in family!".format(p_name))
                
        t.Commit()
        
    msg = "Successfully mapped {} annotations!\n\n".format(mapped_count)
    if errors:
        msg += "ERRORS/SKIPPED:\n" + "\n".join(errors)
        
    TaskDialog.Show("Mapping Result", msg)

if __name__ == '__main__':
    main()
