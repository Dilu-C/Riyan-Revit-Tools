# -*- coding: utf-8 -*-
"""
Riyan Family Material Auditor & Standardizer
Scans all families in active Revit Document or Master RVTs.
Detects legacy non-standard materials and standardizes them to RYN_MAT standards.
Compatible with Autodesk Revit 2021 through Revit 2027+.
"""
import os
import json
import codecs
import clr

clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")
import Autodesk.Revit.DB as DB
from pyrevit import forms

# Standard RYN Material Mapping Dictionary
# Maps legacy/inconsistent material names to official RYN_MAT standard names
STANDARD_MATERIAL_MAP = {
    # Door Frames
    "door - frame - alum": "RYN_MAT_DoorFrame_Aluminium",
    "door - frame": "RYN_MAT_DoorFrame_Aluminium",
    "door-frame-alum": "RYN_MAT_DoorFrame_Aluminium",
    "alum - door frame": "RYN_MAT_DoorFrame_Aluminium",
    "door frame - timber": "RYN_MAT_DoorFrame_Timber",
    "door frame timber": "RYN_MAT_DoorFrame_Timber",
    "wood - frame": "RYN_MAT_DoorFrame_Timber",

    # Door Leaves / Panels
    "door - panel in timber": "RYN_MAT_DoorPanel_Timber",
    "door panel in timber": "RYN_MAT_DoorPanel_Timber",
    "door - panel - timber": "RYN_MAT_DoorPanel_Timber",
    "door - panel": "RYN_MAT_DoorPanel_Timber",
    "door - leaf": "RYN_MAT_DoorPanel_Timber",
    "door leaf": "RYN_MAT_DoorPanel_Timber",
    "door - frame - alum (leaf)": "RYN_MAT_DoorPanel_Aluminium",

    # Glass
    "door - glass": "RYN_MAT_Glass",
    "door glass": "RYN_MAT_Glass",
    "window panel - glass": "RYN_MAT_Glass",
    "glass": "RYN_MAT_Glass",
    "clear glass": "RYN_MAT_Glass",

    # Louvers
    "door panel louver": "RYN_MAT_DoorPanel_Louver_Aluminium",
    "louver - alum": "RYN_MAT_DoorPanel_Louver_Aluminium",
    "louver": "RYN_MAT_DoorPanel_Louver_Aluminium",

    # Window Frames
    "window frame - alum": "RYN_MAT_WindowFrame_Aluminium",
    "window - frame - alum": "RYN_MAT_WindowFrame_Aluminium",
    "window frame": "RYN_MAT_WindowFrame_Aluminium",
    "window panel frame - alum": "RYN_MAT_WindowPanelFrame_Aluminium"
}

EXPECTED_DOOR_PARAMS = [
    "RYN_Material_DoorFrame",
    "RYN_Material_DoorLeaf",
    "RYN_Material_Glass"
]

EXPECTED_WINDOW_PARAMS = [
    "RYN_Material_WindowFrame",
    "RYN_Material_WindowPanelFrame",
    "RYN_Material_Glass"
]

def audit_document_materials(doc):
    """Audits all loadable families in doc for material parameters and consistency."""
    collector = DB.FilteredElementCollector(doc).OfClass(DB.Family)
    
    audit_results = {
        "doc_title": doc.Title,
        "total_families": 0,
        "compliant_families": [],
        "inconsistent_materials": [],
        "missing_parameters": []
    }

    # Get all materials in doc for quick lookup
    mat_collector = DB.FilteredElementCollector(doc).OfClass(DB.Material)
    doc_materials = {m.Name.upper(): m.Id for m in mat_collector}

    for fam in collector:
        if fam.IsInPlace:
            continue

        fam_name = fam.Name
        cat_name = fam.FamilyCategory.Name if fam.FamilyCategory else "Unknown"
        audit_results["total_families"] += 1

        is_door = "DOOR" in fam_name.upper() or cat_name == "Doors"
        is_window = "WIN" in fam_name.upper() or cat_name == "Windows"

        expected_params = []
        if is_door:
            expected_params = EXPECTED_DOOR_PARAMS
        elif is_window:
            expected_params = EXPECTED_WINDOW_PARAMS

        symbols = fam.GetFamilySymbolIds()
        if not symbols or symbols.Count == 0:
            continue

        # Inspect first symbol
        sym = doc.GetElement(symbols[0])
        existing_param_names = [p.Definition.Name for p in sym.Parameters]

        # Check missing parameters
        missing = [ep for ep in expected_params if ep not in existing_param_names]
        if missing:
            audit_results["missing_parameters"].append({
                "family": fam_name,
                "category": cat_name,
                "missing": missing
            })

        # Check material values assigned
        found_inconsistent = False
        mat_details = {}
        for p in sym.Parameters:
            p_name = p.Definition.Name
            is_mat = "Material" in p_name or "MAT" in p_name
            if is_mat:
                m_id = p.AsElementId()
                m_name = "None"
                if m_id and m_id != DB.ElementId.InvalidElementId:
                    m_elem = doc.GetElement(m_id)
                    if m_elem:
                        m_name = m_elem.Name

                mat_details[p_name] = m_name

                # Check if it violates RYN_MAT standard
                if m_name != "None" and not m_name.startswith("RYN_MAT_"):
                    found_inconsistent = True

        if found_inconsistent:
            audit_results["inconsistent_materials"].append({
                "family": fam_name,
                "category": cat_name,
                "materials": mat_details
            })
        elif not missing:
            audit_results["compliant_families"].append(fam_name)

    return audit_results

def apply_material_standardization(doc, audit_results):
    """Automatically reassigns standardized RYN_MAT materials to families."""
    t = DB.Transaction(doc, "Standardize Riyan Materials (RYN_MAT)")
    t.Start()

    mat_collector = DB.FilteredElementCollector(doc).OfClass(DB.Material)
    doc_materials = {m.Name.lower(): m.Id for m in mat_collector}

    updated_count = 0
    for item in audit_results.get("inconsistent_materials", []):
        fam_name = item["family"]
        # Find family in doc
        fam_collector = DB.FilteredElementCollector(doc).OfClass(DB.Family)
        target_fam = None
        for f in fam_collector:
            if f.Name == fam_name:
                target_fam = f
                break

        if not target_fam:
            continue

        for sym_id in target_fam.GetFamilySymbolIds():
            sym = doc.GetElement(sym_id)
            for p in sym.Parameters:
                p_name = p.Definition.Name
                if "Material" in p_name:
                    m_id = p.AsElementId()
                    if m_id and m_id != DB.ElementId.InvalidElementId:
                        m_elem = doc.GetElement(m_id)
                        if m_elem:
                            curr_name_lower = m_elem.Name.lower()
                            if curr_name_lower in STANDARD_MATERIAL_MAP:
                                standard_name = STANDARD_MATERIAL_MAP[curr_name_lower]
                                # Check if standard material exists in doc
                                if standard_name.lower() in doc_materials:
                                    std_id = doc_materials[standard_name.lower()]
                                    p.Set(std_id)
                                    updated_count += 1

    t.Commit()
    return updated_count
