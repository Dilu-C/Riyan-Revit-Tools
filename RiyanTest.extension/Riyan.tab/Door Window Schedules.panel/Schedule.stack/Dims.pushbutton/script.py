# -*- coding: utf-8 -*-
__title__ = 'Dimensions'
__doc__ = 'Adds dimensions to generated 2D schedule tables in Plan and Elevation views.'

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
    if "Sill Height" in names:
        p = el.get_Parameter(DB.BuiltInParameter.INSTANCE_SILL_HEIGHT_PARAM)
        if p and p.HasValue:
            if p.StorageType == DB.StorageType.Double: 
                v = p.AsDouble()
                if v > 100.0: return v / 304.8
                return v
    if "Head Height" in names:
        p = el.get_Parameter(DB.BuiltInParameter.INSTANCE_HEAD_HEIGHT_PARAM)
        if p and p.HasValue:
            if p.StorageType == DB.StorageType.Double: 
                v = p.AsDouble()
                if v > 100.0: return v / 304.8
                return v
    for n in names:
        p = el.LookupParameter(n)
        if not p: p = el_type.LookupParameter(n)
        if p and p.HasValue:
            if p.StorageType == DB.StorageType.Double:
                v = p.AsDouble()
                if v > 100.0: return v / 304.8
                return v
            if p.StorageType == DB.StorageType.String:
                s = p.AsString()
                if s:
                    import re
                    m = re.search(r'[\d\.]+', s)
                    if m: return float(m.group(0)) / 304.8
    return 0.0

def round_to_5mm(feet_val):
    if feet_val <= 0: return feet_val
    mm_val = feet_val * 304.8
    rounded_mm = round(mm_val / 5.0) * 5.0
    return rounded_mm / 304.8

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

def create_real_dimension(doc, view, p1, p2, offset_dir, offset_dist, ls_el, text_below=None, text_above=None):
    try:
        # Minimal reference lines AT the dimension location
        # to avoid touching the architectural geometry (Revit min curve length is 1/300 ft ~ 1.016 mm)
        half_len = 0.6 / 304.8
        dl1_start = p1 + offset_dir * (offset_dist - half_len)
        dl1_end   = p1 + offset_dir * (offset_dist + half_len)
        dl1 = create_invisible_line(doc, view, dl1_start, dl1_end, ls_el)

        dl2_start = p2 + offset_dir * (offset_dist - half_len)
        dl2_end   = p2 + offset_dir * (offset_dist + half_len)
        dl2 = create_invisible_line(doc, view, dl2_start, dl2_end, ls_el)

        doc.Regenerate()
        ref_arr = DB.ReferenceArray()
        ref_arr.Append(dl1.GeometryCurve.Reference)
        ref_arr.Append(dl2.GeometryCurve.Reference)

        dim_line = DB.Line.CreateBound(p1 + offset_dir * offset_dist, p2 + offset_dir * offset_dist)
        dim = doc.Create.NewDimension(view, dim_line, ref_arr)
        if text_below: dim.Below = text_below
        if text_above: dim.Above = text_above
        
        return dim
    except Exception as e: 
        return None

def auto_dimension_component(doc, view, model_el, comp, is_plan, is_door):
    if not comp: 
        return
    t_id = model_el.GetTypeId()
    if t_id == DB.ElementId.InvalidElementId:
        t_id = model_el.Id
        el_type = model_el
    else:
        el_type = doc.GetElement(t_id)
    
    w = get_param_val_dim(model_el, el_type, ["Rough Width", "Width", "Opening Width"])
    h = get_param_val_dim(model_el, el_type, ["Rough Height", "Height", "Opening Height"])

    
    panel_w = get_param_val_dim(model_el, el_type, ["RYN_Door_PanelWidth", "RYN_WIN_PanelWidth", "Panel Width"])
    panel_w = round_to_5mm(panel_w)
    panel_h = get_param_val_dim(model_el, el_type, ["RYN_Door_PanelHeight", "RYN_WIN_PanelHeight", "Panel Height"])
    panel_h = round_to_5mm(panel_h)
    
    frame_depth = get_param_val_dim(model_el, el_type, ["RYN_Door_FrameDepth", "RYN_WIN_FrameDepth", "Frame Depth", "RYN_WIN_PanelFrameThickness"])
    is_frameless = False
    if "FRAMELESS" in el_type.FamilyName.upper() or (hasattr(el_type, "Name") and "FRAMELESS" in el_type.Name.upper()):
        is_frameless = True
    if "OPENING" in el_type.FamilyName.upper() or (hasattr(el_type, "Name") and "OPENING" in el_type.Name.upper()):
        is_frameless = True
    
    if frame_depth <= 0 and not is_frameless: 
        frame_depth = 50.0 / 304.8
    
    sill = get_param_val_dim(model_el, el_type, ["Sill Height"])
    if sill <= 0.01:
        head_h = get_param_val_dim(model_el, el_type, ["Head Height"])
        if head_h > 0 and h > 0:
            sill = head_h - h
    
    box = comp.get_BoundingBox(view)
    if not box:
        return
    comp_w = box.Max.X - box.Min.X
    comp_h = box.Max.Y - box.Min.Y
    
    if w <= 0: w = comp_w
    if h <= 0: h = comp_h
    center_x = (box.Min.X + box.Max.X) / 2.0
    bottom_y = box.Min.Y
    if not is_plan and not is_door and sill > 0:
        bottom_y -= sill
    
    left_x = center_x - (w / 2.0)
    right_x = center_x + (w / 2.0)
    
    ls_el = get_white_line_style(doc)
    
    if is_plan:
        d1_dist = (200.0 if not is_door else 150.0) / 304.8
        d2_dist = d1_dist + (400.0 / 304.8)
        
        # 1st Dim: Panel Width (starts inside by frame depth, only 1 panel wide)
        p_left_x = left_x + frame_depth
        p_right_x = p_left_x + panel_w
        if panel_w > 0 and not is_frameless and abs(panel_w - w) > 0.01:
            create_real_dimension(doc, view, DB.XYZ(p_left_x, bottom_y, 0), DB.XYZ(p_right_x, bottom_y, 0), DB.XYZ(0, -1, 0), d1_dist, ls_el, "PANEL WIDTH")
            
        # 2nd Dim: Wall Opening
        create_real_dimension(doc, view, DB.XYZ(left_x, bottom_y, 0), DB.XYZ(right_x, bottom_y, 0), DB.XYZ(0, -1, 0), d2_dist, ls_el, "WALL OPENING")
    else:
        top_y = bottom_y + h
        
        d1_dist = 300.0 / 304.8
        d2_dist = d1_dist + (400.0 / 304.8)
        
        if is_door:
            # 1st Dim: Panel Height
            p_bottom_y = bottom_y
            p_top_y = p_bottom_y + panel_h
            if panel_h > 0 and not is_frameless and abs(panel_h - h) > 0.01:
                create_real_dimension(doc, view, DB.XYZ(right_x, p_bottom_y, 0), DB.XYZ(right_x, p_top_y, 0), DB.XYZ(1, 0, 0), d1_dist, ls_el, "PANEL HEIGHT")
                
            # 2nd Dim: Wall Opening
            create_real_dimension(doc, view, DB.XYZ(right_x, bottom_y, 0), DB.XYZ(right_x, top_y, 0), DB.XYZ(1, 0, 0), d2_dist, ls_el, "WALL OPENING")
            
            # Panel text note logic
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
                    num_panels = 1
                    if panel_w > 0: num_panels = int(round(w / panel_w))
                    if num_panels < 1: num_panels = 1
                    
                    opts = DB.TextNoteOptions()
                    opts.HorizontalAlignment = DB.HorizontalTextAlignment.Center
                    opts.VerticalAlignment = DB.VerticalTextAlignment.Middle
                    opts.TypeId = doc.GetDefaultElementTypeId(DB.ElementTypeGroup.TextNoteType)
                    step = w / float(num_panels)
                    for i in range(num_panels):
                        p_center_x = left_x + (step / 2.0) + (i * step)
                        DB.TextNote.Create(doc, view.Id, DB.XYZ(p_center_x, bottom_y + (h * 0.65), 0), abbv, opts)
        else:
            # For windows
            window_bottom = bottom_y + sill
            window_top = window_bottom + h
            
            # RIGHT SIDE dims (dakunu pette)
            # d1 (300mm): PANEL HEIGHT
            p_bottom_y = window_bottom + frame_depth
            p_top_y = p_bottom_y + panel_h
            if panel_h > 0 and not is_frameless and abs(panel_h - h) > 0.01:
                create_real_dimension(doc, view, DB.XYZ(right_x, p_bottom_y, 0), DB.XYZ(right_x, p_top_y, 0), DB.XYZ(1, 0, 0), d1_dist, ls_el, "PANEL HEIGHT")
            
            # d2 (700mm): WALL OPENING
            create_real_dimension(doc, view, DB.XYZ(right_x, window_bottom, 0), DB.XYZ(right_x, window_top, 0), DB.XYZ(1, 0, 0), d2_dist, ls_el, "WALL OPENING")
            
            # d3 (700mm): SILL HEIGHT - FFL to window bottom
            if sill > 0.01:
                create_real_dimension(doc, view, DB.XYZ(right_x, bottom_y, 0), DB.XYZ(right_x, window_bottom, 0), DB.XYZ(1, 0, 0), d2_dist, ls_el, "SILL HEIGHT")
            
            # LEFT SIDE dim (wam patte)
            # d4 (300mm): HEAD HEIGHT - FFL to window top
            create_real_dimension(doc, view, DB.XYZ(left_x, bottom_y, 0), DB.XYZ(left_x, window_top, 0), DB.XYZ(-1, 0, 0), d1_dist, ls_el, "HEAD HEIGHT")


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
    generic = DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_GenericModel).WhereElementIsNotElementType().ToElements()
    
    model_types = {}
    model_instances = {}
    for el_inst in list(doors) + list(windows) + list(generic):
        t_id = el_inst.GetTypeId()
        if t_id != DB.ElementId.InvalidElementId and t_id not in model_types:
            model_types[t_id] = doc.GetElement(t_id)
            model_instances[t_id] = el_inst
                
    updated_count = 0
    with DB.Transaction(doc, "Dimension Tables") as t:
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
                        if l.GeometryCurve.Length < (20.0 / 304.8):
                            doc.Delete(l.Id)
                    except: pass
        
        for c_el in tables_to_update:
            tag_p = c_el.LookupParameter("RYN_Schedule_Tag")
            if not tag_p or not tag_p.HasValue: continue
            table_tag = tag_p.AsString()
            matching_t_ids = []
            for t_id, el in model_types.items():
                el_type = doc.GetElement(t_id) if (t_id and t_id != DB.ElementId.InvalidElementId) else el
                p = el_type.get_Parameter(DB.BuiltInParameter.ALL_MODEL_TYPE_MARK)
                if p and p.HasValue and p.AsString() == table_tag:
                    matching_t_ids.append(t_id)
                    
            if not matching_t_ids:
                continue
                
            c_view = doc.GetElement(c_el.OwnerViewId)
            
            leg_comps = DB.FilteredElementCollector(doc, c_el.OwnerViewId).OfCategory(DB.BuiltInCategory.OST_LegendComponents).ToElements()
            for lc in leg_comps:
                lc_t = lc.get_Parameter(DB.BuiltInParameter.LEGEND_COMPONENT).AsElementId()
                if lc_t in matching_t_ids:
                    model_el = model_instances.get(lc_t, doc.GetElement(lc_t))
                    dir_param = lc.get_Parameter(DB.BuiltInParameter.LEGEND_COMPONENT_VIEW)
                    val_str = dir_param.AsValueString() if dir_param else ""
                    is_plan = ("Plan" in val_str) if val_str else False
                    is_door = (model_el.Category.Id.IntegerValue == int(DB.BuiltInCategory.OST_Doors)) if model_el.Category else True
                    auto_dimension_component(doc, c_view, model_el, lc, is_plan, is_door)
                    
            updated_count += 1
        status = t.Commit()
    forms.alert("Successfully added dimensions to {} schedule tables!".format(updated_count))

if __name__ == "__main__":
    main()










































