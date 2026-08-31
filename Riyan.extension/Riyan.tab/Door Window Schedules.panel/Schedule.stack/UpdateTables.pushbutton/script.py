# -*- coding: utf-8 -*-
__title__ = 'Update\nTables'
__doc__ = 'Syncs existing 2D schedule tables with the latest data from the 3D model.'

import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
from Autodesk.Revit.DB import *
from pyrevit import revit, DB
from pyrevit import forms

doc = revit.doc

# ==========================================
# AUTO DIMENSION ENGINE
# ==========================================
def get_param_val_dim(el, el_type, names):
    for name in names:
        p = el.LookupParameter(name)
        if not p: p = el_type.LookupParameter(name)
        if p and p.HasValue: return p.AsDouble()
    return 0.0

def get_white_line_style(doc):
    cats = doc.Settings.Categories
    lines_cat = cats.get_Item(DB.BuiltInCategory.OST_Lines)
    if lines_cat.SubCategories.Contains("RYN_DimRef"):
        return lines_cat.SubCategories.get_Item("RYN_DimRef").GetGraphicsStyle(DB.GraphicsStyleType.Projection)
    try:
        new_cat = cats.NewSubcategory(lines_cat, "RYN_DimRef")
        new_cat.LineColor = DB.Color(255, 255, 255)
        return new_cat.GetGraphicsStyle(DB.GraphicsStyleType.Projection)
    except: return None

def create_invisible_line(doc, view, p1, p2, ls_el):
    line = DB.Line.CreateBound(p1, p2)
    dc = doc.Create.NewDetailCurve(view, line)
    if ls_el:
        try: dc.LineStyle = ls_el
        except: pass
    return dc

def get_dim_snap_dist(doc):
    dt = doc.GetElement(doc.GetDefaultElementTypeId(DB.ElementTypeGroup.LinearDimensionType))
    if dt:
        p = dt.get_Parameter(DB.BuiltInParameter.DIM_STYLE_DIM_LINE_SNAP_DIST)
        if p: return p.AsDouble()
    return 8.0 / 304.8

def create_real_dimension(doc, view, p1, p2, offset_dir, offset_dist, ls_el, text_below=None, text_above=None):
    try:
        dl1 = create_invisible_line(doc, view, p1 - offset_dir * 0.5, p1 + offset_dir * 0.5, ls_el)
        dl2 = create_invisible_line(doc, view, p2 - offset_dir * 0.5, p2 + offset_dir * 0.5, ls_el)
        ref_arr = DB.ReferenceArray()
        ref_arr.Append(dl1.GeometryCurve.Reference)
        ref_arr.Append(dl2.GeometryCurve.Reference)
        dim_line = DB.Line.CreateBound(p1 + (offset_dir * offset_dist), p2 + (offset_dir * offset_dist))
        dim = doc.Create.NewDimension(view, dim_line, ref_arr)
        if text_below: dim.Below = text_below
        if text_above: dim.Above = text_above
        return dim
    except: return None

def auto_dimension_component(doc, view, model_el, comp, is_plan, is_door, absolute_center_x=None, absolute_bottom_y=None):
    if not comp: return
    t_id = model_el.GetTypeId()
    el_type = doc.GetElement(t_id)
    
    w = get_param_val_dim(model_el, el_type, ["Rough Width", "Width"])
    h = get_param_val_dim(model_el, el_type, ["Rough Height", "Height"])
    panel_w = get_param_val_dim(model_el, el_type, ["Panel Width", "Width"])
    panel_h = get_param_val_dim(model_el, el_type, ["Panel Height", "Height"])
    sill = get_param_val_dim(model_el, el_type, ["Sill Height"])
    
    if w == 0: return
    if h == 0: return
    
    num_panels = 1
    if panel_w > 0 and w > 0:
        num_panels = int(round(w / panel_w))
        if num_panels < 1: num_panels = 1
    p_num = get_param_val_dim(model_el, el_type, ["Number of Panels", "No of Panels", "Panels", "Number of Doors", "No. of Panels"])
    if p_num > 0: num_panels = int(p_num)
    
    if panel_w == 0 or panel_w > w: panel_w = w / float(num_panels)
    if panel_h == 0 or panel_h > h: panel_h = h
    
    if absolute_center_x is None:
        box = comp.get_BoundingBox(view)
        if not box: return
        center_x = (box.Min.X + box.Max.X) / 2.0
        bottom_y = box.Min.Y
    else:
        center_x = absolute_center_x
        bottom_y = absolute_bottom_y
    left_x = center_x - (w / 2.0)
    right_x = center_x + (w / 2.0)
    
    ls_el = get_white_line_style(doc)
    snap = get_dim_snap_dist(doc)
    
    if is_plan:
        d1_dist = 150.0 / 304.8
        d2_dist = d1_dist + snap
        
        p_left_x = left_x
        p_right_x = left_x + panel_w
        
        create_real_dimension(doc, view, DB.XYZ(p_left_x, bottom_y, 0), DB.XYZ(p_right_x, bottom_y, 0), DB.XYZ(0, -1, 0), d1_dist, ls_el, "PANEL WIDTH")
        create_real_dimension(doc, view, DB.XYZ(left_x, bottom_y, 0), DB.XYZ(right_x, bottom_y, 0), DB.XYZ(0, -1, 0), d2_dist, ls_el, "WALL OPENING")
    else:
        top_y = bottom_y + h
        p_top_y = bottom_y + panel_h
        
        d1_dist = 300.0 / 304.8
        d2_dist = d1_dist + snap
        
        if is_door:
            create_real_dimension(doc, view, DB.XYZ(right_x, bottom_y, 0), DB.XYZ(right_x, p_top_y, 0), DB.XYZ(1, 0, 0), d1_dist, ls_el, "PANEL HEIGHT")
            create_real_dimension(doc, view, DB.XYZ(right_x, bottom_y, 0), DB.XYZ(right_x, top_y, 0), DB.XYZ(1, 0, 0), d2_dist, ls_el, "WALL OPENING")
            
            int_panel = model_el.LookupParameter("Internal panel type")
            if not int_panel: int_panel = el_type.LookupParameter("Internal panel type")
            if int_panel and int_panel.HasValue:
                val = int_panel.AsString().upper()
                abbv = ""
                if "SOLID TIMBER" in val: abbv = "ST"
                elif "FROSTED" in val: abbv = "FG"
                elif "TEMPERED" in val or "CLEAR" in val: abbv = "TG"
                elif "LOUVER" in val: abbv = "AL"
                elif "GALVANIZED" in val: abbv = "GS"
                elif "PVC" in val or "POLYVINYL" in val: abbv = "PVC"
                elif "TIMBER" in val: abbv = "T"
                
                if abbv:
                    opts = DB.TextNoteOptions()
                    opts.HorizontalAlignment = DB.HorizontalTextAlignment.Center
                    opts.VerticalAlignment = DB.VerticalTextAlignment.Middle
                    opts.TypeId = doc.GetDefaultElementTypeId(DB.ElementTypeGroup.TextNoteType)
                    step = w / float(num_panels)
                    for i in range(num_panels):
                        p_center_x = left_x + (step / 2.0) + (i * step)
                        DB.TextNote.Create(doc, view.Id, DB.XYZ(p_center_x, bottom_y + (h * 0.65), 0), abbv, opts)
        else:
            window_bottom = bottom_y + sill
            window_top = window_bottom + h
            create_real_dimension(doc, view, DB.XYZ(right_x, bottom_y, 0), DB.XYZ(right_x, window_bottom, 0), DB.XYZ(1, 0, 0), d1_dist, ls_el, "SILL HEIGHT")
            create_real_dimension(doc, view, DB.XYZ(right_x, window_bottom, 0), DB.XYZ(right_x, window_top, 0), DB.XYZ(1, 0, 0), d2_dist, ls_el, "WALL OPENING")

def main():
    detail_items = DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_DetailComponents).WhereElementIsNotElementType().ToElements()
    
    tables_to_update = []
    for di in detail_items:
        if hasattr(di, "Symbol") and di.Symbol:
            fname = di.Symbol.FamilyName.upper()
            if "DOORSCHEDULE" in fname.replace(" ", "") or "WINDOWSCHEDULE" in fname.replace(" ", ""):
                tables_to_update.append(di)
                
    if not tables_to_update:
        forms.alert("No generated schedule tables found in the project!")
        return
        
    doors = DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Doors).WhereElementIsNotElementType().ToElements()
    windows = DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Windows).WhereElementIsNotElementType().ToElements()
    
    model_types = {}
    type_instances = {}
    
    for el in list(doors) + list(windows):
        t_id = el.GetTypeId()
        if t_id != DB.ElementId.InvalidElementId:
            if el.OwnerViewId != DB.ElementId.InvalidElementId and doc.GetElement(el.OwnerViewId).ViewType == DB.ViewType.Legend:
                continue
            if t_id not in model_types:
                model_types[t_id] = el
            if t_id not in type_instances:
                type_instances[t_id] = []
            type_instances[t_id].append(el)
                
    updated_count = 0
    with DB.Transaction(doc, "Sync Table Data") as t:
        t.Start()
        
        # CLEAR EXISTING DIMS & NOTES
        views_to_clean = set()
        for c_el in tables_to_update:
            views_to_clean.add(c_el.OwnerViewId)
            
        for v_id in views_to_clean:
            v_dims = DB.FilteredElementCollector(doc, v_id).OfClass(DB.Dimension).ToElements()
            for d in v_dims:
                if d.GroupId == DB.ElementId.InvalidElementId:
                    try: doc.Delete(d.Id)
                    except: pass
            v_texts = DB.FilteredElementCollector(doc, v_id).OfClass(DB.TextNote).ToElements()
            for text_note in v_texts:
                if len(text_note.Text) <= 4 and text_note.GroupId == DB.ElementId.InvalidElementId:
                    try: doc.Delete(text_note.Id)
                    except: pass
            v_lines = DB.FilteredElementCollector(doc, v_id).OfClass(DB.CurveElement).ToElements()
            for l in v_lines:
                if l.GroupId == DB.ElementId.InvalidElementId:
                    try:
                        if l.GeometryCurve.Length < (10.0 / 304.8):
                            doc.Delete(l.Id)
                    except: pass
        
        for c_el in tables_to_update:
            tag_p = c_el.LookupParameter("RYN_Schedule_Tag")
            if not tag_p or not tag_p.HasValue: continue
            table_tag = tag_p.AsString()
            
            model_el = None
            model_t_id = None
            for t_id, el in model_types.items():
                el_type = doc.GetElement(t_id)
                p = el_type.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_MARK)
                if p and p.HasValue and p.AsString() == table_tag:
                    model_el = el
                    model_t_id = t_id
                    break
                    
            if not model_el: continue
                
            for p in c_el.Parameters:
                p_name = p.Definition.Name
                if "RYN_" in p_name and not p.IsReadOnly and p_name != "RYN_Schedule_Tag":
                    src_p = model_el.LookupParameter(p_name)
                    if not src_p: src_p = model_el.LookupParameter(p_name.replace("RYN_Schedule_", "RYN_Door_Schedule_"))
                    if not src_p: src_p = model_el.LookupParameter(p_name.replace("RYN_Schedule_", "RYN_Window_Schedule_"))
                    
                    if "Location" in p_name:
                        locs = []
                        if model_t_id in type_instances:
                            for i_el in type_instances[model_t_id]:
                                i_loc_p = i_el.LookupParameter(p_name)
                                if not i_loc_p: i_loc_p = i_el.LookupParameter(p_name.replace("RYN_Schedule_", "RYN_Door_Schedule_"))
                                if not i_loc_p: i_loc_p = i_el.LookupParameter(p_name.replace("RYN_Schedule_", "RYN_Window_Schedule_"))
                                if i_loc_p and i_loc_p.HasValue:
                                    val = i_loc_p.AsString()
                                    if val and val not in locs:
                                        locs.append(val)
                        if locs:
                            prefix = ""
                            rooms = []
                            for l in locs:
                                if " - " in l:
                                    parts = l.split(" - ", 1)
                                    if not prefix: prefix = parts[0] + " - "
                                    if parts[1] not in rooms: rooms.append(parts[1])
                                else:
                                    if l not in rooms: rooms.append(l)
                            p.Set(prefix + ", ".join(rooms))
                    else:
                        if src_p and src_p.HasValue:
                            if src_p.StorageType == DB.StorageType.String: p.Set(src_p.AsString())
                            elif src_p.StorageType == DB.StorageType.Integer: p.Set(src_p.AsInteger())
                            elif src_p.StorageType == DB.StorageType.Double: p.Set(src_p.AsDouble())
                            elif src_p.StorageType == DB.StorageType.ElementId: p.Set(src_p.AsElementId())
                            
            # Update auto dimensions
            c_view = doc.GetElement(c_el.OwnerViewId)
            is_door = "DOOR" in c_el.Symbol.FamilyName.upper()
            
            leg_comps = DB.FilteredElementCollector(doc, c_el.OwnerViewId).OfCategory(DB.BuiltInCategory.OST_LegendComponents).ToElements()
            for lc in leg_comps:
                lc_t = lc.get_Parameter(DB.BuiltInParameter.LEGEND_COMPONENT).AsElementId()
                if lc_t == model_t_id:
                    dir_param = lc.get_Parameter(DB.BuiltInParameter.LEGEND_COMPONENT_VIEW)
                    val_str = dir_param.AsValueString() if dir_param else ""
                    is_plan = ("Plan" in val_str) if val_str else False
                    # TEMPORARILY DISABLED
                    # auto_dimension_component(doc, c_view, model_el, lc, is_plan, is_door)
                    
            updated_count += 1
            
        t.Commit()
        
    forms.alert("Successfully updated {} schedule tables with the latest 3D model data!".format(updated_count))

if __name__ == "__main__":
    main()
