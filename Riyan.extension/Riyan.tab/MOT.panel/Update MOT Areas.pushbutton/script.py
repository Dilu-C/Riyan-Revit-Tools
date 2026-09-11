# -*- coding: utf-8 -*-
__title__ = "Update MOT\nAreas"
__doc__ = "Calculates total Covered (Building Common Area) and Open (Exterior Area) areas and writes them to Project Information parameters for the MOT Schedule."

import re
from pyrevit import revit, DB, UI, forms

doc = revit.doc

def main():
    # 1. Find the target view
    views = DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Views).WhereElementIsNotElementType().ToElements()
    target_view = None
    for v in views:
        if v.IsTemplate:
            continue
        v_name = v.Name.upper()
        title_param = v.get_Parameter(DB.BuiltInParameter.VIEW_DESCRIPTION)
        v_title = title_param.AsString().upper() if title_param and title_param.AsString() else ""
        
        if "TOTAL BUA PER UNIT" in v_name or "TOTAL BUA PER UNIT" in v_title:
            target_view = v
            break
            
    if not target_view:
        forms.alert("Could not find an Area Plan view named 'TOTAL BUA PER UNIT'.", title="View Not Found", warn_icon=True)
        return

    # 2. Collect areas visible in the TARGET VIEW for calculation
    areas_in_view = DB.FilteredElementCollector(doc, target_view.Id).OfCategory(DB.BuiltInCategory.OST_Areas).WhereElementIsNotElementType().ToElements()

    if not areas_in_view:
        forms.alert("No areas found in the view '{}'.".format(target_view.Name), title="No Areas Found", warn_icon=True)
        return

    covered_area = 0.0
    open_area = 0.0

    for area in areas_in_view:
        if area.Area > 0:
            param = area.get_Parameter(DB.BuiltInParameter.AREA_TYPE)
            if param:
                val_str = param.AsValueString()
                area_val = area.Area
                if val_str == "Building Common Area":
                    covered_area += area_val
                elif val_str == "Exterior Area":
                    open_area += area_val

    # Convert sq ft to sq m (Revit internal unit for area is sq ft)
    sqm_factor = 0.09290304
    covered_area_sqm = covered_area * sqm_factor
    open_area_sqm = open_area * sqm_factor

    # 3. Write to Area elements and Auto-Update MOT Schedule Title
    with revit.Transaction("Update MOT Areas & Schedule"):
        def set_param(p, value_internal):
            if not p:
                return
                
            value_sqm = value_internal * 0.09290304
            
            if p.StorageType == DB.StorageType.String:
                p.Set(str(round(value_sqm, 2)))
            elif p.StorageType == DB.StorageType.Double:
                is_area = False
                try:
                    if hasattr(p.Definition, "GetDataType"):
                        is_area = ("area" in str(p.Definition.GetDataType().TypeId).lower())
                    elif hasattr(p.Definition, "ParameterType"):
                        is_area = (str(p.Definition.ParameterType) == "Area")
                except:
                    pass
                    
                if is_area:
                    p.Set(value_internal) # Area parameter expects internal units (sq ft)
                else:
                    p.Set(value_sqm) # Number parameter expects the actual number
            else:
                p.Set(value_sqm)
                
        # Write to ALL areas in the project so the schedule updates regardless of which area it uses
        all_areas = DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Areas).WhereElementIsNotElementType().ToElements()
        
        updated_count = 0
        for area in all_areas:
            param_covered = area.LookupParameter("COVERED / MOT AREA PER UNIT (SQM)")
            param_open = area.LookupParameter("OPEN AREA PER UNIT (SQM)")
            
            if param_covered or param_open:
                set_param(param_covered, covered_area)
                set_param(param_open, open_area)
                updated_count += 1
                
        if updated_count == 0:
            forms.alert("Please ensure the following Project Parameters are assigned to the 'Areas' category:\n\n- COVERED / MOT AREA PER UNIT (SQM)\n- OPEN AREA PER UNIT (SQM)", title="Missing Parameters", warn_icon=True)
            return

        # 4. Format Schedule Title: <Building Number> - <Building Code> - <Building Name>
        p_info = doc.ProjectInformation
        pn_num = p_info.LookupParameter("RYN_PrInfo_BuildingNumber") if p_info else None
        pn_name = p_info.LookupParameter("RYN_PrInfo_BuildingName") if p_info else None
        pn_code = p_info.LookupParameter("RYN_PrInfo_BuildingCode") if p_info else None

        s_num = pn_num.AsString().strip() if pn_num and pn_num.AsString() else ""
        s_code = pn_code.AsString().strip() if pn_code and pn_code.AsString() else ""
        s_name = pn_name.AsString().strip() if pn_name and pn_name.AsString() else ""

        # Fallback to Building Name on Project Information if RYN param empty
        if not s_name and p_info:
            p_std_name = p_info.LookupParameter("Building Name")
            if p_std_name and p_std_name.AsString():
                s_name = p_std_name.AsString().strip()

        # Fallback extraction from document Title / Filename
        if not s_num or not s_code:
            file_name = doc.Title or ""
            m_bldg = re.search(r'[-_](\d{2}[A-Za-z]?)[-_]\(([^\)]+)\)', file_name)
            if m_bldg:
                f_num, f_code = m_bldg.groups()
                if not s_num:
                    s_num = f_num
                if not s_code:
                    s_code = "({})".format(f_code.strip("()"))

        mot_title_parts = [pt for pt in [s_num, s_code, s_name] if pt]
        mot_new_title = " - ".join(mot_title_parts) if mot_title_parts else ""

        # Update MOT Schedule header and view name
        updated_schedules = []
        if mot_new_title:
            doc_schedules = DB.FilteredElementCollector(doc).OfClass(DB.ViewSchedule).ToElements()
            for ds in doc_schedules:
                if ds.IsTemplate:
                    continue
                is_target = False
                ds_name = ds.Name.upper()
                if "BUILDING NAME" in ds_name or "BDN" in ds_name or "MOT" in ds_name or "AREA PER UNIT" in ds_name:
                    is_target = True
                else:
                    try:
                        f_count = ds.Definition.GetFieldCount()
                        for i in range(f_count):
                            f = ds.Definition.GetField(i)
                            fn = f.GetName().upper()
                            fh = (f.ColumnHeading or "").upper()
                            if "MOT" in fn or "MOT" in fh or "COVERED / MOT" in fn or "COVERED / MOT" in fh:
                                is_target = True
                                break
                    except Exception:
                        pass

                if is_target:
                    try:
                        t_data = ds.GetTableData()
                        sec_h = t_data.GetSectionData(DB.SectionType.Header)
                        if sec_h:
                            sec_h.SetCellType(0, 0, DB.CellType.Text)
                            sec_h.SetCellText(0, 0, mot_new_title)
                        if ds.Name != mot_new_title:
                            try:
                                ds.Name = mot_new_title
                            except Exception:
                                pass
                        updated_schedules.append(ds.Name)
                    except Exception:
                        pass
            
    msg = "Successfully updated MOT Areas & Schedule!\n\n"
    msg += "• Covered Area: {:.2f} sqm\n".format(covered_area_sqm)
    msg += "• Open Area: {:.2f} sqm\n\n".format(open_area_sqm)
    if updated_schedules:
        msg += "• Schedule Header Updated:\n  '{}'".format(mot_new_title)
    elif mot_new_title:
        msg += "• Schedule Title Generated:\n  '{}'".format(mot_new_title)
    forms.alert(msg, title="Success")

if __name__ == '__main__':
    main()
