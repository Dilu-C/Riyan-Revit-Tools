# -*- coding: utf-8 -*-
from Autodesk.Revit.DB import *
from pyrevit import revit, DB, forms

doc = revit.doc

def set_param(element, param_base, value):
    if not value: return
    p = element.LookupParameter("RYN_Schedule_" + param_base)
    if not p: p = element.LookupParameter("RYN_Door_Schedule_" + param_base)
    if not p: p = element.LookupParameter("RYN_Window_Schedule_" + param_base)
    if p and not p.IsReadOnly:
        p.Set(value)

def get_room_center(room):
    if room.Location and hasattr(room.Location, "Point"): return room.Location.Point
    bb = room.get_BoundingBox(None)
    if bb: return (bb.Min + bb.Max) / 2.0
    return None

def get_room_name(element):
    to_room = None
    from_room = None
    phase_id = element.CreatedPhaseId
    if phase_id != ElementId.InvalidElementId:
        phase = doc.GetElement(phase_id)
        to_room = element.get_ToRoom(phase)
        from_room = element.get_FromRoom(phase)
            
    if not to_room and not from_room and doc.ActiveView:
        try:
            if hasattr(doc.ActiveView, 'Phase') and doc.ActiveView.Phase:
                to_room = element.get_ToRoom(doc.ActiveView.Phase)
                from_room = element.get_FromRoom(doc.ActiveView.Phase)
        except: pass
        
    selected_room = None
    if to_room and from_room:
        host = element.Host
        if host and isinstance(host, DB.Wall):
            wall_dir = host.Orientation
            interior_dir = DB.XYZ(-wall_dir.X, -wall_dir.Y, -wall_dir.Z)
            door_pt = element.Location.Point if element.Location and hasattr(element.Location, "Point") else None
            pt_to = get_room_center(to_room)
            pt_from = get_room_center(from_room)
            if door_pt and pt_to and pt_from:
                if (pt_to - door_pt).DotProduct(interior_dir) > (pt_from - door_pt).DotProduct(interior_dir):
                    selected_room = to_room
                else:
                    selected_room = from_room
            else: selected_room = to_room
        else: selected_room = to_room
    elif to_room: selected_room = to_room
    elif from_room: selected_room = from_room
        
    if selected_room:
        name_param = selected_room.get_Parameter(BuiltInParameter.ROOM_NAME)
        if name_param: return name_param.AsString()
    return None

def get_type_mark(el_type):
    if el_type:
        tm_param = el_type.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_MARK)
        if tm_param and tm_param.HasValue: return tm_param.AsString()
    return None

def get_param_val(element, el_type, param_names):
    for p_name in param_names:
        if el_type:
            p = el_type.LookupParameter(p_name)
            if p and p.HasValue: return p.AsDouble()
        p = element.LookupParameter(p_name)
        if p and p.HasValue: return p.AsDouble()
    return None

def get_opening_dim(element, el_type):
    w_val = get_param_val(element, el_type, ["Rough Width", "Width"])
    h_val = get_param_val(element, el_type, ["Rough Height", "Height"])
    if w_val and h_val:
        w_mm = int(round(w_val * 304.8))
        h_mm = int(round(h_val * 304.8))
        return "{}x{}mm (W x H)".format(w_mm, h_mm)
    return None

def main():
    if doc.IsFamilyDocument:
        forms.alert("This tool is meant to be run in the Project environment.")
        return

    doors = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Doors).WhereElementIsNotElementType().ToElements()
    windows = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Windows).WhereElementIsNotElementType().ToElements()
    elements = list(doors) + list(windows)
    
    type_counts = {}
    for el in elements:
        t_id = el.GetTypeId().IntegerValue
        type_counts[t_id] = type_counts.get(t_id, 0) + 1
    
        building_code = ""
    if doc.ProjectInformation:
        bc_param = doc.ProjectInformation.LookupParameter("RYN_PrInfo_BuildingCode")
        if bc_param and bc_param.HasValue:
            building_code = bc_param.AsString()
            
    with DB.Transaction(doc, "Auto-Populate All Data") as t:
        t.Start()
        for el in elements:
            el_type = None
            try: el_type = doc.GetElement(el.GetTypeId())
            except: pass
            
            # 1. Location
            room_name = get_room_name(el)
            if room_name:
                prefix = (building_code + " - ") if building_code else ""
                set_param(el, "Location", prefix + room_name)
                    
            # 2. Tag
            type_mark = get_type_mark(el_type)
            if type_mark: set_param(el, "Tag", type_mark)
                    
            # 3. Wall Opening Dim
            dim_str = get_opening_dim(el, el_type)
            if dim_str: set_param(el, "Wall opening dim.", dim_str)
                    
            # 4. Type (Description)
            desc = ""
            if el_type:
                desc_p = el_type.get_Parameter(BuiltInParameter.ALL_MODEL_DESCRIPTION)
                if desc_p and desc_p.HasValue:
                    desc = desc_p.AsString()
                    if desc:
                        clean_desc = desc.replace("-", " ").replace("_", " ").upper()
                        import re
                        clean_desc = re.sub(" +", " ", clean_desc).strip()
                        # Extract only up to DOOR or WINDOW to drop the material parts
                        match = re.search(r"^(.*?(?:DOOR|WINDOW))", clean_desc)
                        if match:
                            clean_desc = match.group(1).strip()
                        set_param(el, "Type", clean_desc)
                    
            # 5. Quantity
            count = type_counts.get(el.GetTypeId().IntegerValue, 0)
            if count > 0:
                qty_str = "{:02d} NOS.".format(count)
                set_param(el, "Quantity", qty_str)
                
            # 6. Open Area
            w_val = get_param_val(el, el_type, ["Rough Width", "Width"])
            h_val = get_param_val(el, el_type, ["Rough Height", "Height"])
            if w_val and h_val:
                area_sqm = (w_val * 0.3048) * (h_val * 0.3048)
                set_param(el, "Open area", "{:.2f} Sqm".format(area_sqm))
                
            # 7. Frame Size (50 x Wall Thickness)
            frame_w = 50
            frame_d = 150
            if el.Host and hasattr(el.Host, "Width"):
                frame_d = int(round(el.Host.Width * 304.8))
            frame_size_str = "{}x{}mm".format(frame_w, frame_d)
            set_param(el, "Frame size", frame_size_str)

            # 8. Material Logic (from August 7 backup)
            desc_lower = desc.lower() if desc else ""
            frame_mat = ""
            frame_fin = ""
            panel_mat = ""
            panel_fin = ""
            int_panel = ""
            
            if "timber" in desc_lower:
                frame_mat = "SOLID TIMBER"
                frame_fin = "TIMBER FINISH"
                panel_mat = "SOLID TIMBER"
                panel_fin = "TIMBER FINISH"
                int_panel = "SOLID TIMBER PANEL"
            elif "aluminium" in desc_lower or "aluminum" in desc_lower:
                frame_mat = "80 MICRON POWDER COATED ALUMINUM"
                frame_fin = "GRAY : MATTE FINISH"
                panel_mat = "80 MICRON POWDER COATED ALUMINUM"
                panel_fin = "GRAY : MATTE FINISH"
                if "louvers" in desc_lower: int_panel = "ALUMINIUM LOUVERS"
            elif "frameless" in desc_lower:
                frame_mat = "(N/A)"
                frame_fin = "(N/A)"
                panel_mat = "(N/A)"
                panel_fin = "(N/A)"
            elif "galvanized" in desc_lower:
                frame_mat = "GALVANIZED STEEL"
                frame_fin = "GALVANIZED STEEL"
                panel_mat = "GALVANIZED STEEL"
                panel_fin = "GALVANIZED STEEL"
                int_panel = "GALVANIZED STEEL PANEL"
                
            if "frosted glass" in desc_lower:
                int_panel = "12 mm THK TEMPERED FROSTED GLASS"
                
            set_param(el, "Frame material", frame_mat)
            set_param(el, "Frame finish", frame_fin)
            set_param(el, "Door panel material", panel_mat)
            set_param(el, "Door panel finish", panel_fin)
            set_param(el, "Window panel material", panel_mat)
            set_param(el, "Window panel finish", panel_fin)
            set_param(el, "Internal panel type", int_panel)
            
            # 8. Fixed Hardware & Ratings
            set_param(el, "Fire rating", "1HR")
            set_param(el, "Acoustic rating", "(N/A)")
            
            hardware = "HAFFLE OR EQUIVALENT"
            set_param(el, "Hinges/ sliding gear", hardware)
            set_param(el, "Hinges/sliding gear", hardware)
            set_param(el, "Handle", hardware)
            set_param(el, "Lock set", hardware)
            
            set_param(el, "Door viewer", "(N/A)")
            set_param(el, "Door closer", "YES")
            set_param(el, "Soft closing", "YES")
            set_param(el, "Flush bolts", "YES")
            set_param(el, "Door stopper", "YES")
            set_param(el, "Rubber seal", "YES")
            set_param(el, "Kick plate", "NO")
            set_param(el, "Access control", "CARD ACCESS")

        t.Commit()
        
    forms.alert("Recovered & Generated Data for ALL 25 Parameters Successfully!")

if __name__ == '__main__':
    main()













