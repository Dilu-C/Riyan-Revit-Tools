# -*- coding: utf-8 -*-
from pyrevit import revit, DB, forms
import System.Windows
import os
import re

doc = revit.doc
uidoc = revit.uidoc

def get_next_name(base_name, count):
    match = re.search(r'(\d+)$', base_name)
    if match:
        s_len = len(match.group(1))
        prefix = base_name[:-s_len]
        return prefix + str(count).zfill(s_len)
    else:
        return base_name + " - %02d" % count

def get_unique_view_name(doc, base_name, count):
    while True:
        test_name = get_next_name(base_name, count)
        existing = [v for v in DB.FilteredElementCollector(doc).OfClass(DB.View).ToElements() if not isinstance(v, DB.ViewSheet)]
        found = False
        for v in existing:
            if v.Name == test_name:
                found = True
                break
        if not found:
            return test_name, count
        count += 1
        
def get_unique_sheet_number(doc, base_number, count, skip_sheet_id=None):
    while True:
        test_num = get_next_name(base_number, count)
        existing = DB.FilteredElementCollector(doc).OfClass(DB.ViewSheet).ToElements()
        found = False
        for s in existing:
            if skip_sheet_id and s.Id == skip_sheet_id:
                continue
            if s.SheetNumber == test_num:
                found = True
                break
        if not found:
            return test_num, count
        count += 1

class LegendGenForm(forms.WPFWindow):
    def __init__(self, xaml_path):
        forms.WPFWindow.__init__(self, xaml_path)
        btn_gen = self.FindName("BtnGenerate")
        btn_cancel = self.FindName("BtnCancel")
        if btn_gen: btn_gen.Click += self.BtnGenerate_Click
        if btn_cancel: btn_cancel.Click += self.BtnCancel_Click

    def get_is_door(self):
        combo = self.FindName("ComboCategory")
        if combo: return combo.Text == "Doors"
        return True

    def BtnCancel_Click(self, sender, e):
        self.Close()

    def BtnGenerate_Click(self, sender, e):
        if getattr(self, 'is_done', False):
            self.Close()
            return
        try:
            txt_prog = self.FindName("TxtProgress")
            is_door = self.get_is_door()
            cat_enum = DB.BuiltInCategory.OST_Doors if is_door else DB.BuiltInCategory.OST_Windows
            table_name = "RYN_DetailItem_DoorSchedule" if is_door else "RYN_DetailItem_WindowSchedule"
            sel_ids = uidoc.Selection.GetElementIds()
            if not sel_ids: return
            
            pristine_view = doc.ActiveView
            alignment_tasks = []
            base_sheet = None
            base_legend_viewport = None
            base_notes_viewport = None
            base_schedule_instance = None
            
            viewports = DB.FilteredElementCollector(doc).OfClass(DB.Viewport).ToElements()
            for vp in viewports:
                if vp.ViewId == pristine_view.Id:
                    base_sheet = doc.GetElement(vp.SheetId)
                    base_legend_viewport = vp
                    break
                    
            if not base_sheet:
                forms.alert("Please place your Template Legend View on a Sheet first, so I can use it as a template!")
                return
                
            # Find other viewports on the base sheet
            all_vps = [doc.GetElement(v_id) for v_id in base_sheet.GetAllViewports()]
            for vp in all_vps:
                view = doc.GetElement(vp.ViewId)
                if "NOTES" in view.Name.upper() and vp.Id != base_legend_viewport.Id:
                    base_notes_viewport = vp
                    
            # Find schedule on base sheet (excluding Revision Schedules which have no filters)
            ssis = DB.FilteredElementCollector(doc, base_sheet.Id).OfClass(DB.ScheduleSheetInstance).ToElements()
            base_schedule_view = None
            base_schedule_instance = None
            for ssi in ssis:
                sched = doc.GetElement(ssi.ScheduleId)
                if sched and sched.Definition:
                    cat_id = sched.Definition.CategoryId
                    # Ensure it is a Door/Window schedule, not a Revision schedule
                    if cat_id.IntegerValue == int(cat_enum):
                        base_schedule_instance = ssi
                        base_schedule_view = sched
                        break
                
            # Find Titleblock
            tblocks = DB.FilteredElementCollector(doc, base_sheet.Id).OfCategory(DB.BuiltInCategory.OST_TitleBlocks).ToElements()
            tblock_id = tblocks[0].GetTypeId() if len(tblocks) > 0 else DB.ElementId.InvalidElementId
            if tblock_id == DB.ElementId.InvalidElementId:
                forms.alert("No Titleblock found on the base sheet!")
                return
                
            min_y = 1e9; max_y = -1e9
            for eid in sel_ids:
                el = doc.GetElement(eid)
                bbox = el.get_BoundingBox(pristine_view)
                if bbox:
                    min_y = min(min_y, bbox.Min.Y)
                    max_y = max(max_y, bbox.Max.Y)
                
            padding_y = 1000.0 / 304.8
            padding_x = 500.0 / 304.8
            y_spacing = (max_y - min_y) + padding_y
                
            model_elements = DB.FilteredElementCollector(doc).OfCategory(cat_enum).WhereElementIsNotElementType().ToElements()
            unique_types = {}
            for el in model_elements:
                t_id = el.GetTypeId()
                if t_id != DB.ElementId.InvalidElementId and t_id not in unique_types:
                    unique_types[t_id] = el
                    
            if len(unique_types) == 0:
                return
                
            # Verify the Parameter for filtering
            test_instance = list(unique_types.values())[0]
            sheet_param = test_instance.LookupParameter("RYN_Schedule_SheetNumber")
            if not sheet_param:
                forms.alert("Please add the 'RYN_Schedule_SheetNumber' parameter (Text type) to your Door Types first!")
                return
                
            # field_id check moved inside transaction
                    
            template_elev_comp = None
            template_plan_comp = None
            template_table = None
            for eid in sel_ids:
                el = doc.GetElement(eid)
                if el.Category and el.Category.Id.IntegerValue == int(DB.BuiltInCategory.OST_LegendComponents):
                    dir_param = el.get_Parameter(DB.BuiltInParameter.LEGEND_COMPONENT_VIEW)
                    if dir_param:
                        val_str = dir_param.AsValueString()
                        if val_str and "Plan" in val_str:
                            template_plan_comp = el
                        elif val_str and "Elevation" in val_str:
                            template_elev_comp = el
                elif el.Category and el.Category.Id.IntegerValue == int(DB.BuiltInCategory.OST_DetailComponents):
                    if hasattr(el, "Symbol") and el.Symbol and (el.Name == table_name or table_name in el.Symbol.FamilyName):
                        template_table = el
                    elif el.LookupParameter("WIDTH") or el.LookupParameter("Width"):
                        template_table = el
                        
            if not template_plan_comp or not template_table: return
            
            pbox = template_plan_comp.get_BoundingBox(pristine_view)
            template_plan_center_y = (pbox.Min.Y + pbox.Max.Y) / 2.0
            plan_view_id = template_plan_comp.get_Parameter(DB.BuiltInParameter.LEGEND_COMPONENT_VIEW).AsElementId()
            
            tbox = template_table.get_BoundingBox(pristine_view)
            template_table_left_x = tbox.Min.X
            template_table_top_y = tbox.Max.Y
            if template_elev_comp:
                ebox = template_elev_comp.get_BoundingBox(pristine_view)
                template_elev_bottom_y = ebox.Min.Y
                ffl_gap = template_elev_bottom_y - template_table_top_y
            else:
                template_elev_bottom_y = tbox.Max.Y + (500.0/304.8)
                ffl_gap = 500.0/304.8
            
            if template_elev_comp:
                elev_view_id = template_elev_comp.get_Parameter(DB.BuiltInParameter.LEGEND_COMPONENT_VIEW).AsElementId()
            else:
                elev_view_id = DB.ElementId.InvalidElementId
            
            current_x = 0.0
            current_y = 0.0
            row_count = 0
            MAX_ROW_WIDTH = 28500.0 / 304.8
            sheet_count = 1
            
            current_sheet_number = base_sheet.SheetNumber
            
            with DB.Transaction(doc, "Generate Legends & Sheets") as t:
                t.Start()
                
                field_id = None
                if base_schedule_view:
                    definition = base_schedule_view.Definition
                    for i in range(definition.GetFieldCount()):
                        field = definition.GetField(i)
                        if field.ParameterId == sheet_param.Id:
                            field_id = field.FieldId
                            break
                            
                    if not field_id:
                        try:
                            sched_field = definition.AddField(DB.ScheduleFieldType.Instance, sheet_param.Id)
                            sched_field.IsHidden = True
                            field_id = sched_field.FieldId
                        except Exception as e:
                            forms.alert("Failed to auto-add field to schedule: " + str(e))
                            t.RollBack()
                            return

                    if base_schedule_view and field_id:
                        import re
                        if not re.search(r'\d+$', base_schedule_view.Name):
                            try:
                                new_base_sched_id = base_schedule_view.Duplicate(DB.ViewDuplicateOption.Duplicate)
                                new_base_sched = doc.GetElement(new_base_sched_id)
                                new_base_sched.Name = base_schedule_view.Name + " - 01"
                                
                                new_def = new_base_sched.Definition
                                new_def.ClearFilters()
                                new_def.AddFilter(DB.ScheduleFilter(field_id, DB.ScheduleFilterType.Equal, base_sheet.SheetNumber))
                                
                                loc = base_schedule_instance.Point
                                doc.Delete(base_schedule_instance.Id)
                                base_schedule_instance = DB.ScheduleSheetInstance.Create(doc, base_sheet.Id, new_base_sched_id, loc)
                            except: pass

                # Cleanup old dimensions & texts from previous runs on the template view
                v_lines = DB.FilteredElementCollector(doc, pristine_view.Id).OfClass(DB.CurveElement).ToElements()
                for l in v_lines:
                    try:
                        if l.LineStyle and l.LineStyle.Name == 'RYN_DimRef' and l.GroupId == DB.ElementId.InvalidElementId:
                            doc.Delete(l.Id)
                    except: pass
                v_dims = DB.FilteredElementCollector(doc, pristine_view.Id).OfClass(DB.Dimension).ToElements()
                for d in v_dims:
                    try:
                        if hasattr(d, 'Below') and d.Below in ['PANEL WIDTH', 'WALL OPENING', 'PANEL HEIGHT', 'SILL HEIGHT', 'HEAD HEIGHT']:
                            if d.GroupId == DB.ElementId.InvalidElementId:
                                doc.Delete(d.Id)
                    except: pass
                v_texts = DB.FilteredElementCollector(doc, pristine_view.Id).OfClass(DB.TextNote).ToElements()
                for txt_el in v_texts:
                    try:
                        if txt_el.Text in ['ST', 'FG', 'TG', 'AL', 'GS', 'PVC', 'T']:
                            if txt_el.GroupId == DB.ElementId.InvalidElementId:
                                doc.Delete(txt_el.Id)
                    except: pass
                  # CREATE A PERFECTLY CLEAN BACKUP (ONLY TITLEBLOCK)
                if base_schedule_instance and base_notes_viewport: alignment_tasks.append((base_schedule_instance, base_notes_viewport, base_sheet))
                clean_backup_id = pristine_view.Duplicate(DB.ViewDuplicateOption.WithDetailing)
                clean_backup = doc.GetElement(clean_backup_id)
                
                from System.Collections.Generic import List
                template_ids_in_backup = List[DB.ElementId]()
                
                for eid in sel_ids:
                    orig_el = doc.GetElement(eid)
                    if not orig_el: continue
                    orig_bbox = orig_el.get_BoundingBox(pristine_view)
                    orig_center = None
                    if orig_bbox:
                        orig_center = (orig_bbox.Min + orig_bbox.Max) / 2.0
                    elif orig_el.Location and hasattr(orig_el.Location, "Point"):
                        orig_center = orig_el.Location.Point
                    
                    if orig_center:
                        collector = DB.FilteredElementCollector(doc, clean_backup_id).OfCategoryId(orig_el.Category.Id)
                        for backup_el in collector:
                            backup_bbox = backup_el.get_BoundingBox(clean_backup)
                            backup_center = None
                            if backup_bbox:
                                backup_center = (backup_bbox.Min + backup_bbox.Max) / 2.0
                            elif backup_el.Location and hasattr(backup_el.Location, "Point"):
                                backup_center = backup_el.Location.Point
                                
                            if backup_center and orig_center.DistanceTo(backup_center) < 0.1:
                                template_ids_in_backup.Add(backup_el.Id)
                                break
                
                # We no longer delete template elements from clean_backup because we reuse them!
                
                current_view = pristine_view
                
                row_width_used = 0.0
                prev_width = 0.0
                is_first_in_row = True
                
                elements_to_delete_in_current_view = []
                
                def is_tall(el):
                    try:
                        p = el.LookupParameter("Height")
                        if not p: p = el.LookupParameter("Rough Height")
                        if not p: 
                            t_el = doc.GetElement(el.GetTypeId())
                            if t_el:
                                p = t_el.LookupParameter("Height")
                                if not p: p = t_el.get_Parameter(DB.BuiltInParameter.DOOR_HEIGHT)
                        if p and p.AsDouble() > (2900.0 / 304.8):
                            return 1
                    except: pass
                    return 0
                    
                global_max_door_height_ft = 0.0
                for t_id, model_el in unique_types.items():
                    try:
                        p = model_el.LookupParameter("Height")
                        if not p: p = model_el.LookupParameter("Rough Height")
                        if not p: 
                            t_el = doc.GetElement(t_id)
                            if t_el:
                                p = t_el.LookupParameter("Height")
                                if not p: p = t_el.get_Parameter(DB.BuiltInParameter.DOOR_HEIGHT)
                        if p and p.AsDouble() > global_max_door_height_ft:
                            global_max_door_height_ft = p.AsDouble()
                    except: pass
                
                tall_table_height_ft = global_max_door_height_ft + (1000.0 / 304.8)
                    
                sorted_items = sorted(unique_types.items(), key=lambda x: (is_tall(x[1]), natural_sort_key(get_type_mark(x[1], doc))))
                # default table height from bounding box
                default_table_height_ft = max_y - min_y
                current_row_max_height = default_table_height_ft
                
                for t_id, model_el in sorted_items:
                    f_type = doc.GetElement(t_id)
                    d_width_val = 900.0 / 304.8
                    d_height_val = 2100.0 / 304.8
                    
                    try:
                        wp = None
                        hp = None
                        for p in f_type.Parameters:
                            try:
                                if p.Definition and p.StorageType == DB.StorageType.Double:
                                    if p.Definition.Name == "Width" and p.AsDouble() > 0:
                                        wp = p
                                    elif p.Definition.Name == "Height" and p.AsDouble() > 0:
                                        hp = p
                            except: pass
                                    
                        if not wp: wp = f_type.get_Parameter(DB.BuiltInParameter.DOOR_WIDTH)
                        if not hp: hp = f_type.get_Parameter(DB.BuiltInParameter.DOOR_HEIGHT)
                            
                        if wp and wp.AsDouble() > 0: d_width_val = wp.AsDouble()
                        if hp and hp.AsDouble() > 0: d_height_val = hp.AsDouble()
                    except: pass
                    
                    # Set the Sheet Number parameter on the Door Type!
                    try:
                        # Set it on ALL instances of this type
                        inst_collector = DB.FilteredElementCollector(doc).OfCategory(cat_enum).WhereElementIsNotElementType().ToElements()
                        for i_el in inst_collector:
                            if i_el.GetTypeId() == t_id:
                                p = i_el.LookupParameter("RYN_Schedule_SheetNumber")
                                if p and not p.IsReadOnly:
                                    p.Set(current_sheet_number)
                    except:
                        pass
                    
                    t_width_ft = max(5300.0 / 304.8, d_width_val + (2000.0 / 304.8))
                    is_tall_door = is_tall(model_el)
                    if is_tall_door:
                        t_height_ft = max(default_table_height_ft, tall_table_height_ft)
                        delta_height = t_height_ft - default_table_height_ft
                    else:
                        t_height_ft = default_table_height_ft
                        delta_height = 0.0
                    
                    if is_first_in_row:
                        current_x = 0.0
                        row_width_used = t_width_ft
                        current_row_max_height = t_height_ft
                    else:
                        if row_width_used + padding_x + t_width_ft > MAX_ROW_WIDTH:
                            current_x = 0.0
                            row_width_used = t_width_ft
                            current_y -= (current_row_max_height + padding_y)
                            
                            if current_row_max_height > default_table_height_ft + 0.1:
                                row_count = 2
                            else:
                                row_count += 1
                                
                            current_row_max_height = t_height_ft
                            
                            if row_count >= 2:
                                elements_to_delete_in_current_view = []
                                sheet_count += 1
                                try:
                                    # Create new Sheet First (to resolve any number conflicts)
                                    new_sheet = DB.ViewSheet.Create(doc, tblock_id)
                                    new_sheet.SheetNumber, sheet_count = get_unique_sheet_number(doc, base_sheet.SheetNumber, sheet_count, new_sheet.Id)
                                    new_sheet.Name = get_next_name(base_sheet.Name, sheet_count)
                                    
                                    # Support Revit 2025 Sheet Collections
                                    try:
                                        if hasattr(base_sheet, 'SheetCollectionId') and hasattr(new_sheet, 'SheetCollectionId'):
                                            new_sheet.SheetCollectionId = base_sheet.SheetCollectionId
                                    except:
                                        pass
                                    
                                    # Copy organizational parameters from base sheet to new sheet
                                    for p in base_sheet.Parameters:
                                        if not p.IsReadOnly and p.Id.IntegerValue > 0 and p.Definition.Name not in ["Sheet Number", "Sheet Name"]:
                                            new_p = new_sheet.LookupParameter(p.Definition.Name)
                                            if new_p and not new_p.IsReadOnly:
                                                if p.StorageType == DB.StorageType.String:
                                                    new_p.Set(p.AsString() or "")
                                                elif p.StorageType == DB.StorageType.Integer:
                                                    new_p.Set(p.AsInteger())
                                    
                                    # Create new Legend View using the resolved sheet_count
                                    new_view_id = clean_backup.Duplicate(DB.ViewDuplicateOption.WithDetailing)
                                    current_view = doc.GetElement(new_view_id)
                                    current_view.Name, _ = get_unique_view_name(doc, pristine_view.Name, sheet_count)
                                    safe_categories = set([doc.GetElement(e_id).Category.Id.IntegerValue for e_id in sel_ids if doc.GetElement(e_id) and doc.GetElement(e_id).Category])
                                    temp_v_elements = DB.FilteredElementCollector(doc, current_view.Id).WhereElementIsNotElementType().ToElements()
                                    elements_to_delete_in_current_view = [e.Id for e in temp_v_elements if e.Category and e.Category.Id.IntegerValue in safe_categories]
                                    current_sheet_number = new_sheet.SheetNumber
                                    
                                    # Place Legend View on new Sheet
                                    new_leg_vp = DB.Viewport.Create(doc, new_sheet.Id, current_view.Id, base_legend_viewport.GetBoxCenter())
                                    if new_leg_vp and base_legend_viewport:
                                        try: new_leg_vp.ChangeTypeId(base_legend_viewport.GetTypeId())
                                        except: pass
                                        
                                        # Re-align based on Top-Left corner instead of Center
                                        doc.Regenerate()
                                        base_outline = base_legend_viewport.GetBoxOutline()
                                        new_outline = new_leg_vp.GetBoxOutline()
                                        
                                        base_tl = DB.XYZ(base_outline.MinimumPoint.X, base_outline.MaximumPoint.Y, 0)
                                        new_tl = DB.XYZ(new_outline.MinimumPoint.X, new_outline.MaximumPoint.Y, 0)
                                        
                                        translation = base_tl - new_tl
                                        DB.ElementTransformUtils.MoveElement(doc, new_leg_vp.Id, translation)
                                        

                                    
                                    # Duplicate & Place Schedule First
                                    new_ssi = None
                                    new_notes_vp = None
                                    
                                    with DB.SubTransaction(doc) as st:
                                        st.Start()
                                        if base_schedule_view and field_id:
                                            new_sched_id = base_schedule_view.Duplicate(DB.ViewDuplicateOption.Duplicate)
                                            current_schedule = doc.GetElement(new_sched_id)
                                            current_schedule.Name, _ = get_unique_view_name(doc, base_schedule_view.Name, sheet_count)
                                            
                                            definition = current_schedule.Definition
                                            definition.ClearFilters()
                                            definition.AddFilter(DB.ScheduleFilter(field_id, DB.ScheduleFilterType.Equal, current_sheet_number))
                                            
                                            new_ssi = DB.ScheduleSheetInstance.Create(doc, new_sheet.Id, current_schedule.Id, base_schedule_instance.Point)
                                            
                                        if base_notes_viewport:
                                            new_notes_vp = DB.Viewport.Create(doc, new_sheet.Id, base_notes_viewport.ViewId, base_notes_viewport.GetBoxCenter())
                                            if new_notes_vp and base_notes_viewport:
                                                try: new_notes_vp.ChangeTypeId(base_notes_viewport.GetTypeId())
                                                except: pass
                                        st.Commit()
                                        
                                    if new_notes_vp and new_ssi:
                                        alignment_tasks.append((new_ssi, new_notes_vp, new_sheet))
                                                
                                except Exception as e:
                                    import traceback
                                    forms.alert("Error creating sheet/views: " + str(e) + "\n\nMake sure you deleted the old generated sheets before running again!")
                                    return
                                current_y = 0.0
                                row_count = 0
                                
                                # Make sure to set the sheet parameter for the CURRENT door (since it shifted to a new sheet)
                                try:
                                    inst_collector = DB.FilteredElementCollector(doc).OfCategory(cat_enum).WhereElementIsNotElementType().ToElements()
                                    for i_el in inst_collector:
                                        if i_el.GetTypeId() == t_id:
                                            p = i_el.LookupParameter("RYN_Schedule_SheetNumber")
                                            if p and not p.IsReadOnly:
                                                p.Set(current_sheet_number)
                                except:
                                    pass
                        else:
                            current_x += prev_width + padding_x
                            row_width_used += padding_x + t_width_ft
                            current_row_max_height = max(current_row_max_height, t_height_ft)
                            
                    offset = DB.XYZ(current_x, current_y, 0)
                    prev_width = t_width_ft
                    is_first_in_row = False
                    
                    new_plan_comp = None
                    new_elev_comp = None
                    new_table = None
                    elevation_text_note = None
                    
                    try:
                        from System.Collections.Generic import List
                                
                        current_template_ids = sel_ids if current_view.Id == pristine_view.Id else elements_to_delete_in_current_view
                        
                        if offset.GetLength() < 0.001:
                            copied_ids = current_template_ids
                        else:
                            copied_ids = DB.ElementTransformUtils.CopyElements(doc, List[DB.ElementId](current_template_ids), offset)
                        
                        for cid in copied_ids:
                            c_el = doc.GetElement(cid)
                            if c_el.Category and c_el.Category.Id.IntegerValue == int(DB.BuiltInCategory.OST_LegendComponents):
                                dir_param = c_el.get_Parameter(DB.BuiltInParameter.LEGEND_COMPONENT_VIEW)
                                val_str = dir_param.AsValueString() if dir_param else ""
                                is_plan = ("Plan" in val_str) if val_str else False
                                
                                try:
                                    c_el.ChangeTypeId(t_id)
                                except:
                                    try:
                                        if not is_plan and dir_param and plan_view_id != DB.ElementId.InvalidElementId:
                                            dir_param.Set(plan_view_id)
                                            doc.Regenerate()
                                        
                                        param = c_el.get_Parameter(DB.BuiltInParameter.LEGEND_COMPONENT)
                                        if param:
                                            param.Set(t_id)
                                        doc.Regenerate()
                                        
                                        if not is_plan and dir_param and elev_view_id != DB.ElementId.InvalidElementId:
                                            dir_param.Set(elev_view_id)
                                            doc.Regenerate()
                                    except:
                                        pass
                                    
                                try:
                                    dtl = c_el.get_Parameter(DB.BuiltInParameter.LEGEND_COMPONENT_DETAIL_LEVEL)
                                    if dtl:
                                        dtl.Set(3)
                                except:
                                    pass
                                
                                if is_plan:
                                    new_plan_comp = c_el
                                    try:
                                        hl_param = c_el.LookupParameter("Host Length")
                                        if hl_param and not hl_param.IsReadOnly:
                                            hl_param.Set(d_width_val) 
                                    except:
                                        pass
                                else:
                                    new_elev_comp = c_el
                                    
                            elif c_el.Category and c_el.Category.Id.IntegerValue == int(DB.BuiltInCategory.OST_DetailComponents):
                                is_tbl = False
                                if hasattr(c_el, "Symbol") and c_el.Symbol and (c_el.Name == table_name or table_name in c_el.Symbol.FamilyName):
                                    is_tbl = True
                                elif c_el.LookupParameter("WIDTH") or c_el.LookupParameter("Width") or c_el.LookupParameter("Length"):
                                    is_tbl = True
                                    
                                if is_tbl:
                                    new_table = c_el
                                    
                            elif isinstance(c_el, DB.TextNote):
                                if c_el.Text.strip().upper() == "ELEVATION":
                                    elevation_text_note = c_el
                                    
                        if delta_height > 0.01:
                            shift_vec = DB.XYZ(0, -delta_height / 2.0, 0)
                            if new_elev_comp:
                                DB.ElementTransformUtils.MoveElement(doc, new_elev_comp.Id, shift_vec)
                            if elevation_text_note:
                                DB.ElementTransformUtils.MoveElement(doc, elevation_text_note.Id, shift_vec)
                                
                        if new_table:
                            try:
                                # Set width
                                target_param = None
                                for p in new_table.Parameters:
                                    if p.Definition and p.StorageType == DB.StorageType.Double and not p.IsReadOnly:
                                        p_name = p.Definition.Name.lower()
                                        if "width" in p_name:
                                            target_param = p
                                            break
                                if target_param: target_param.Set(t_width_ft)
                                else:
                                    try: new_table.LookupParameter("WIDTH").Set(t_width_ft)
                                    except: pass
                                
                                try:
                                    h_param = None
                                    for p in new_table.Parameters:
                                        if p.Definition and p.StorageType == DB.StorageType.Double and not p.IsReadOnly:
                                            if "height" in p.Definition.Name.lower():
                                                h_param = p
                                                break
                                    if h_param: h_param.Set(t_height_ft)
                                except: pass
                                    
                                # Set tag so Update Tables can find it!
                                tag_p = new_table.LookupParameter("RYN_Schedule_Tag")
                                if tag_p and not tag_p.IsReadOnly:
                                    f_type = doc.GetElement(t_id); p = f_type.get_Parameter(DB.BuiltInParameter.ALL_MODEL_TYPE_MARK); val = p.AsString() if (p and p.HasValue) else ""; tag_p.Set(val)
                                    
                                # FEED ALL DATA IMMEDIATELY UPON CREATION
                                for p in new_table.Parameters:
                                    p_name = p.Definition.Name
                                    if "RYN_" in p_name and not p.IsReadOnly and p_name != "RYN_Schedule_Tag":
                                        src_p = model_el.LookupParameter(p_name)
                                        if not src_p: src_p = model_el.LookupParameter(p_name.replace("RYN_Schedule_", "RYN_Door_Schedule_"))
                                        if not src_p: src_p = model_el.LookupParameter(p_name.replace("RYN_Schedule_", "RYN_Window_Schedule_"))
                                        
                                        if "Location" in p_name:
                                            locs = []
                                            i_col = DB.FilteredElementCollector(doc).OfCategory(cat_enum).WhereElementIsNotElementType().ToElements()
                                            for i_el in i_col:
                                                if i_el.GetTypeId() == t_id:
                                                    i_loc_p = i_el.LookupParameter(p_name)
                                                    if not i_loc_p: i_loc_p = i_el.LookupParameter(p_name.replace("RYN_Schedule_", "RYN_Door_Schedule_"))
                                                    if not i_loc_p: i_loc_p = i_el.LookupParameter(p_name.replace("RYN_Schedule_", "RYN_Window_Schedule_"))
                                                    if i_loc_p and i_loc_p.HasValue:
                                                        lval = i_loc_p.AsString()
                                                        if lval and lval not in locs: locs.append(lval)
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
                            except: pass
                        doc.Regenerate()
                        
                        target_center_x = template_table_left_x + current_x + (t_width_ft / 2.0)
                        
                        if new_plan_comp:
                            try:
                                npbox = new_plan_comp.get_BoundingBox(current_view)
                                npc_x = (npbox.Min.X + npbox.Max.X) / 2.0
                                dx_plan = target_center_x - npc_x
                                if abs(dx_plan) > 0.001:
                                    DB.ElementTransformUtils.MoveElement(doc, new_plan_comp.Id, DB.XYZ(dx_plan, 0, 0))
                            except: pass
                            
                        if new_elev_comp:
                            try:
                                ebox = new_elev_comp.get_BoundingBox(current_view)
                                ebc_x = (ebox.Min.X + ebox.Max.X) / 2.0
                                dx_elev = target_center_x - ebc_x
                                
                                fname = f_type.FamilyName.upper() if f_type.FamilyName else ""
                                is_sliding = ("SLIDING" in fname) or ("SL" in fname and "SWING" not in fname)
                                
                                target_ffl = template_table_top_y + current_y + ffl_gap
                                target_bottom = target_ffl
                                if is_sliding:
                                    target_bottom -= (50.0 / 304.8)
                                    
                                # INJECTED WINDOW SILL LOGIC
                                if not is_door:
                                    try:
                                        def parse_double(p):
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
                                            
                                        sill_h = 0.0
                                        for pn in ["Sill Height"]:
                                            p = model_el.LookupParameter(pn)
                                            if not p: p = model_el.get_Parameter(DB.BuiltInParameter.INSTANCE_SILL_HEIGHT_PARAM)
                                            if not p: p = f_type.LookupParameter(pn)
                                            if p and p.HasValue:
                                                val = parse_double(p)
                                                if val > 0.01: sill_h = val
                                                
                                        head_h = 0.0
                                        hh = 0.0
                                        
                                        if sill_h <= 0.01:
                                            for pn in ["Head Height"]:
                                                p = model_el.LookupParameter(pn)
                                                if not p: p = model_el.get_Parameter(DB.BuiltInParameter.INSTANCE_HEAD_HEIGHT_PARAM)
                                                if not p: p = f_type.LookupParameter(pn)
                                                if p and p.HasValue: head_h = parse_double(p)
                                            
                                            for pn in ["Rough Height", "Height"]:
                                                p = model_el.LookupParameter(pn)
                                                if not p: p = f_type.LookupParameter(pn)
                                                if p and p.HasValue: 
                                                    hh = parse_double(p)
                                                    if hh > 0.01: break
                                                    
                                            if head_h > 0 and hh > 0:
                                                sill_h = head_h - hh
                                                
                                        if sill_h > 0.01:
                                            target_bottom += sill_h
                                            
                                    except:
                                        pass
                                        
                                dy_elev = target_bottom - ebox.Min.Y
                                
                                if abs(dx_elev) > 0.001 or abs(dy_elev) > 0.001:
                                    DB.ElementTransformUtils.MoveElement(doc, new_elev_comp.Id, DB.XYZ(dx_elev, dy_elev, 0))
                            except: pass
                            
                        doc.Regenerate()
                        try:
                            # Safely pass None to let auto_dim use current bounding boxes!
                            # Temporarily disabled per request to move to separate button
                            # auto_dimension_component(doc, current_view, model_el, new_plan_comp, True, is_door)
                            # auto_dimension_component(doc, current_view, model_el, new_elev_comp, False, is_door)
                            pass
                        except: pass
                                
                    except:
                        pass
                    
                # We no longer delete the template elements because they are used as the first door on each sheet!
                    
                # Delete the clean backup since we don't need it anymore
                try: doc.Delete(clean_backup_id)
                except:
                    pass
                
                doc.Regenerate()
                for ssi, notes_vp, sheet in alignment_tasks:
                    sched_box = ssi.get_BoundingBox(sheet)
                    notes_box = notes_vp.get_BoundingBox(sheet)
                    if sched_box and notes_box:
                        sched_bottom = sched_box.Min.Y
                        notes_top = notes_box.Max.Y
                        target_notes_top = sched_bottom - (10.5 / 304.8)
                        dy = target_notes_top - notes_top
                        if abs(dy) > 0.001:
                            DB.ElementTransformUtils.MoveElement(doc, notes_vp.Id, DB.XYZ(0, dy, 0))
                t.Commit()
                
            with DB.Transaction(doc, "Align Labels") as t2:
                t2.Start()
                # Base sheet absolute positions
                base_box = base_legend_viewport.GetBoxOutline()
                base_tl = DB.XYZ(base_box.MinimumPoint.X, base_box.MaximumPoint.Y, 0)
                base_abs_label = base_legend_viewport.GetBoxCenter() + base_legend_viewport.LabelOffset
                
                for task in alignment_tasks:
                    try:
                        _, _, sheet = task
                        vps = [doc.GetElement(v_id) for v_id in sheet.GetAllViewports()]
                        for vp in vps:
                            view = doc.GetElement(vp.ViewId)
                            if "DOOR SCHEDULE" in view.Name and view.ViewType == DB.ViewType.Legend:
                                # 1. Align Top-Left (now that t1 is committed and box has shrunk)
                                new_box = vp.GetBoxOutline()
                                new_tl = DB.XYZ(new_box.MinimumPoint.X, new_box.MaximumPoint.Y, 0)
                                translation = base_tl - new_tl
                                DB.ElementTransformUtils.MoveElement(doc, vp.Id, translation)
                                
                                # 2. Regenerate to get the true new Center
                                doc.Regenerate()
                                
                                # 3. Set Label position using base relative offset
                                if hasattr(vp, 'LabelOffset') and hasattr(base_legend_viewport, 'LabelOffset'):
                                    vp.LabelOffset = base_legend_viewport.LabelOffset
                                    vp.LabelLineLength = base_legend_viewport.LabelLineLength
                    except: pass
                t2.Commit()
                
            if txt_prog:
                txt_prog.Text = "Legends & Sheets Generated Successfully!"
                txt_prog.Foreground = System.Windows.Media.Brushes.LimeGreen
                
            self.FindName("BtnGenerate").Content = "Done! (Close)"
            self.FindName("BtnGenerate").Background = System.Windows.Media.Brushes.LimeGreen
            self.FindName("BtnGenerate").Foreground = System.Windows.Media.Brushes.Black
            self.is_done = True
        except Exception as ex:
            import traceback
            forms.alert(traceback.format_exc())




















# ==========================================
# AUTO DIMENSION ENGINE
# ==========================================
import re
def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]

def get_type_mark(el, doc):
    t_id = el.GetTypeId()
    t_el = doc.GetElement(t_id)
    p = t_el.LookupParameter("Type Mark")
    if p and p.HasValue: return p.AsString()
    return ""
def get_param_val_str(el, el_type, names):
    for n in names:
        for p in el.Parameters:
            if p.Definition.Name.upper() == n.upper() and p.HasValue:
                return p.AsString() if p.AsString() else p.AsValueString()
        for p in el_type.Parameters:
            if p.Definition.Name.upper() == n.upper() and p.HasValue:
                return p.AsString() if p.AsString() else p.AsValueString()
    return ""
    for n in names:
        for p in el.Parameters:
            if p.Definition.Name.upper() == n.upper() and p.HasValue: return p.AsDouble()
        for p in el_type.Parameters:
            if p.Definition.Name.upper() == n.upper() and p.HasValue: return p.AsDouble()
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

def create_real_dimension(doc, view, p1, p2, offset_dir, offset_dist, max_dist, ls_el, text_below=None, text_above=None):
    try:
        gap = 150.0 / 304.8
        line_len = offset_dist + (150.0 / 304.8)
        
        dl1 = create_invisible_line(doc, view, p1 + offset_dir * gap, p1 + offset_dir * line_len, ls_el)
        dl2 = create_invisible_line(doc, view, p2 + offset_dir * gap, p2 + offset_dir * line_len, ls_el)
        
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
    
    panel_w = get_param_val_dim(model_el, el_type, ["RYN_Door_PanelWidth", "RYN_Window_PanelWidth", "Panel Width", "Width"])
    panel_h = get_param_val_dim(model_el, el_type, ["RYN_Door_PanelHeight", "RYN_Window_PanelHeight", "Panel Height", "Height"])
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
    
    geom_right_x = right_x
    geom_bottom_y = bottom_y
    # cbox override removed to trust math coordinates
    if False:
        geom_right_x = cbox.Max.X
        geom_bottom_y = cbox.Min.Y
        
    ls_el = get_white_line_style(doc)
    
    if is_plan:
        d1_dist = 250.0 / 304.8
        d2_dist = d1_dist + (400.0 / 304.8)
        max_dist = d2_dist
        
        p_left_x = left_x
        p_right_x = left_x + panel_w
        
        if abs(panel_w - w) > 0.01:
            create_real_dimension(doc, view, DB.XYZ(p_left_x, geom_bottom_y, 0), DB.XYZ(p_right_x, geom_bottom_y, 0), DB.XYZ(0, -1, 0), d1_dist, max_dist, ls_el, "PANEL WIDTH")
        create_real_dimension(doc, view, DB.XYZ(left_x, geom_bottom_y, 0), DB.XYZ(right_x, geom_bottom_y, 0), DB.XYZ(0, -1, 0), d2_dist, max_dist, ls_el, "WALL OPENING")
    else:
        top_y = bottom_y + h
        p_top_y = bottom_y + panel_h
        
        d1_dist = 300.0 / 304.8
        d2_dist = d1_dist + (400.0 / 304.8)
        max_dist = d2_dist
        
        if is_door:
            if abs(panel_h - h) > 0.01:
                create_real_dimension(doc, view, DB.XYZ(geom_right_x, bottom_y, 0), DB.XYZ(geom_right_x, p_top_y, 0), DB.XYZ(1, 0, 0), d1_dist, max_dist, ls_el, "PANEL HEIGHT")
            create_real_dimension(doc, view, DB.XYZ(geom_right_x, bottom_y, 0), DB.XYZ(geom_right_x, top_y, 0), DB.XYZ(1, 0, 0), d2_dist, max_dist, ls_el, "WALL OPENING")
            
            val = get_param_val_str(model_el, el_type, ['RYN_Door_InternalPanelType', 'Internal panel type', 'Panel Type']).upper()
            if val:
                abbv = ""
                # replaced
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
            create_real_dimension(doc, view, DB.XYZ(geom_right_x, bottom_y, 0), DB.XYZ(geom_right_x, window_bottom, 0), DB.XYZ(1, 0, 0), d1_dist, max_dist, ls_el, "SILL HEIGHT")
            create_real_dimension(doc, view, DB.XYZ(geom_right_x, window_bottom, 0), DB.XYZ(geom_right_x, window_top, 0), DB.XYZ(1, 0, 0), d2_dist, max_dist, ls_el, "WALL OPENING")

def main():
    if not doc: return
    w = LegendGenForm(os.path.join(os.path.dirname(__file__), "UI.xaml"))
    w.ShowDialog()

if __name__ == '__main__':
    main()








