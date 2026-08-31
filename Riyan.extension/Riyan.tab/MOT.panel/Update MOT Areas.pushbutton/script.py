# -*- coding: utf-8 -*-
__title__ = "Update MOT\nAreas"
__doc__ = "Calculates total Covered (Building Common Area) and Open (Exterior Area) areas and writes them to Project Information parameters for the MOT Schedule."

from pyrevit import revit, DB, UI, forms

doc = revit.doc

def main():
    # Find the target view
    views = DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Views).WhereElementIsNotElementType().ToElements()
    target_view = None
    for v in views:
        if v.IsTemplate:
            continue
        v_name = v.Name.upper()
        # Also check Title on Sheet if available
        title_param = v.get_Parameter(DB.BuiltInParameter.VIEW_DESCRIPTION)
        v_title = title_param.AsString().upper() if title_param and title_param.AsString() else ""
        
        if "TOTAL BUA PER UNIT" in v_name or "TOTAL BUA PER UNIT" in v_title:
            target_view = v
            break
            
    if not target_view:
        forms.alert("Could not find an Area Plan view named 'TOTAL BUA PER UNIT'.", title="View Not Found", warn_icon=True)
        return

    # Only collect areas visible in the TARGET VIEW for calculation
    areas_in_view = DB.FilteredElementCollector(doc, target_view.Id).OfCategory(DB.BuiltInCategory.OST_Areas).WhereElementIsNotElementType().ToElements()

    if not areas_in_view:
        forms.alert("No areas found in the view '{}'.".format(target_view.Name), title="No Areas Found", warn_icon=True)
        return

    covered_area = 0.0
    open_area = 0.0

    for area in areas_in_view:
        # Check if the area is placed
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

    # Write to Area elements
    # Since the user assigned these parameters to the Areas category, we will update ALL areas.
    # That way, the collapsed schedule will show the correct values.
    
    with revit.Transaction("Update MOT Areas"):
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
            
    msg = "Successfully updated MOT Areas!\n\nCovered Area: {} sqm\nOpen Area: {} sqm".format(round(covered_area * 0.09290304, 2), round(open_area * 0.09290304, 2))
    forms.alert(msg, title="Success")

if __name__ == '__main__':
    main()
