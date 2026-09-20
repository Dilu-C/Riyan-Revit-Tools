# -*- coding: utf-8 -*-
"""
pyRevit Hook: doc-saved
Live Dynamic Sync for Riyan Master Library RVT:
- Automatically triggered whenever Dilupa saves the Master Library RVT (Ctrl+S)
- Detects added, edited, and deleted families & wall types
- Renders 100% accurate 3D preview thumbnails via Revit API GetPreviewImage()
- Updates SharePoint catalog.json and local cache instantly with ZERO lag
"""

import os
import sys
import json
import codecs
import re

try:
    import clr
    clr.AddReference("System")
    clr.AddReference("System.Drawing")
    clr.AddReference("RevitAPI")
    import System
    import Autodesk.Revit.DB as DB
except Exception:
    DB = None
    System = None

SHAREPOINT_LIB_ROOT = os.path.expandvars(
    r"%USERPROFILE%\OneDrive - Riyan Private Limited\Riyan LK Projects - 00 - RIYAN REVIT STANDARD\02 LIBRARY"
)
CENTRAL_REPOSITORY = os.path.join(SHAREPOINT_LIB_ROOT, "00 RIYAN FAMILY REPOSITORY")

_this_dir = os.path.dirname(os.path.abspath(__file__))
_repo_root = os.path.abspath(os.path.join(_this_dir, "..", ".."))
LOCAL_CACHE_DIR = os.path.join(_repo_root, "Library_Cache")
if not os.path.exists(LOCAL_CACHE_DIR):
    LOCAL_CACHE_DIR = os.path.expandvars(r"%APPDATA%\pyRevit\Extensions\Riyan-Revit-Tools\Library_Cache")

def is_master_library_doc(doc):
    if not doc:
        return False
    title = (doc.Title or "").upper()
    path = (doc.PathName or "").upper()
    if "RIYAN - LIBRARY" in title or "RIYAN_LIBRARY" in title:
        return True
    if "LIBRARY" in title and "RIYAN" in title:
        return True
    if "RIYAN - LIBRARY FILE" in path or "RIYAN_LIBRARY_ARC" in path or "RIYAN_LIBRARY_STR" in path:
        return True
    return False

def is_sub_component_name(code):
    if not code:
        return False
    c_lower = code.lower()
    if re.search(r'(_pro_|_profile_|profile$|^profile\b|^section profile|^architrave_profile|^c shapes-profile|^gutter profile)', c_lower):
        return True
    if re.search(r'(hardware|handle[std0-9]*$|^hafele\b|^pivot hinge|^stair_hardware)', c_lower):
        if not any(k in c_lower for k in ["cabinet", "table", "chair", "wardrobe"]):
            return True
    if re.match(r'^(door\s*panel|w\s*panel|top\s*panel|mid\s*panel|louver\s*panel|glass\s*panel|panel\s*2|panel\s*with\s*glass|sliding\s*front\s*panel|sliding_door_panel|st-door\s*panel|vv-w_fg\s*-\s*panel|top\s*window\s*panel)', c_lower):
        return True
    return False

def categorize_family_name(code):
    name_up = code.upper()
    disc = "ARCHITECTURAL"
    cat = "General"

    if "STR_" in name_up or "STRUCTURAL" in name_up or "BEAM" in name_up or "REBAR" in name_up:
        disc = "STRUCTURAL"
    elif "PLUMBING" in name_up or "BASIN" in name_up or "TOILET" in name_up or "WC" in name_up:
        disc = "PLUMBING"
    elif "FIRE" in name_up or "SPRINKLER" in name_up:
        disc = "FIRE PROTECTION"
    elif "ACMV" in name_up or "DUCT" in name_up or "DIFFUSER" in name_up:
        disc = "ACMV"
    elif "ELEC" in name_up or "LIGHT" in name_up:
        disc = "ELECTRICAL"

    if disc == "ARCHITECTURAL":
        if "DOR" in name_up or "DOOR" in name_up:
            cat = "Doors"
        elif "WIN" in name_up or "WINDOW" in name_up:
            cat = "Windows"
        elif "WALL" in name_up:
            cat = "Walls"
        elif "TITLEBLOCK" in name_up or "COVERPAGE" in name_up:
            cat = "Annotation-TitleBlocks"
        elif "ANO_" in name_up or "TAG" in name_up:
            cat = "Annotation-Tags"
        elif any(k in name_up for k in ["SOFA", "CHAIR", "TABLE", "FURNITURE"]):
            cat = "Furniture-General"
        elif "COL" in name_up or "COLUMN" in name_up:
            cat = "Architecture-Columns"
        else:
            cat = "Arch-Other"
    elif disc == "STRUCTURAL":
        if "BEAM" in name_up:
            cat = "Structure-Beams"
        elif "COL" in name_up:
            cat = "Structure-Columns"
        elif "REBAR" in name_up:
            cat = "Structure-Rebar"
        else:
            cat = "Structure-General"
    elif disc == "PLUMBING":
        cat = "Plumbing-Fixtures"
    elif disc == "FIRE PROTECTION":
        cat = "Fire-Protection"
    elif disc == "ACMV":
        cat = "ACMV-Equipment"
    elif disc == "ELECTRICAL":
        cat = "Electrical-Fixtures"

    return disc, cat

def sync_master_library_on_save(doc):
    if not doc or not is_master_library_doc(doc):
        return

    # 1. Read existing catalog
    catalog_path = os.path.join(CENTRAL_REPOSITORY, "catalog.json")
    fallback_path = os.path.join(LOCAL_CACHE_DIR, "catalog.json")
    target_path = catalog_path if os.path.exists(catalog_path) else fallback_path

    catalog_items = []
    if os.path.exists(target_path):
        try:
            with codecs.open(target_path, 'r', 'utf-8-sig') as f:
                catalog_items = json.load(f)
        except Exception:
            pass

    # Build lookup
    catalog_dict = {}
    for item in catalog_items:
        c = item.get("code", "").upper()
        if c:
            catalog_dict[c] = item

    doc_path = doc.PathName or ""
    doc_title = doc.Title or os.path.basename(doc_path)
    current_doc_family_names = set()

    # 2. Extract Loadable Families from Document
    families = DB.FilteredElementCollector(doc).OfClass(DB.Family).ToElements()
    for fam in families:
        if fam.IsInPlace:
            continue
        fname = fam.Name
        if is_sub_component_name(fname):
            continue
        
        fname_upper = fname.upper()
        current_doc_family_names.add(fname_upper)

        # Types
        types = []
        try:
            for s_id in fam.GetFamilySymbolIds():
                sym = doc.GetElement(s_id)
                if sym:
                    try:
                        tname = DB.Element.Name.GetValue(sym)
                    except Exception:
                        tname = getattr(sym, "Name", "")
                    if tname:
                        types.append(tname)
        except Exception:
            pass
        if not types:
            types = [fname]

        disc, cat = categorize_family_name(fname)
        if fam.FamilyCategory:
            cname = fam.FamilyCategory.Name
            if "Door" in cname: cat = "Doors"
            elif "Window" in cname: cat = "Windows"
            elif "Furniture" in cname: cat = "Furniture-General"
            elif "Column" in cname: cat = "Architecture-Columns"
            elif "Plumbing" in cname: cat = "Plumbing-Fixtures"

        # 3. 100% Accurate 3D Preview Extraction via Revit API GetPreviewImage()
        thumb_target = os.path.join(CENTRAL_REPOSITORY, "Thumbnails", fname + ".png")
        local_thumb = os.path.join(LOCAL_CACHE_DIR, "Thumbnails", fname + ".png")
        if (not os.path.exists(thumb_target)) and (not os.path.exists(local_thumb)):
            try:
                sym_ids = fam.GetFamilySymbolIds()
                if sym_ids and sym_ids.Count > 0:
                    first_sym = doc.GetElement(sym_ids[0])
                    if first_sym:
                        bmp = first_sym.GetPreviewImage(System.Drawing.Size(256, 256))
                        if bmp:
                            try:
                                os.makedirs(os.path.dirname(thumb_target), exist_ok=True)
                                bmp.Save(thumb_target, System.Drawing.Imaging.ImageFormat.Png)
                            except Exception:
                                pass
                            try:
                                os.makedirs(os.path.dirname(local_thumb), exist_ok=True)
                                bmp.Save(local_thumb, System.Drawing.Imaging.ImageFormat.Png)
                            except Exception:
                                pass
            except Exception:
                pass

        thumb_ref = thumb_target if os.path.exists(thumb_target) else (local_thumb if os.path.exists(local_thumb) else None)

        if fname_upper in catalog_dict:
            # Update existing family
            ex = catalog_dict[fname_upper]
            ex["types"] = types
            ex["category"] = cat
            ex["discipline"] = disc
            ex["source_doc_path"] = doc_path
            ex["source_doc_title"] = doc_title
            ex["is_level_master"] = True
            if thumb_ref:
                ex["thumbnail"] = thumb_ref
        else:
            # Add brand new family
            new_item = {
                "code": fname,
                "title": fname,
                "discipline": disc,
                "category": cat,
                "types": types,
                "badges": [
                    {"label": "Master Library", "icon": u"⭐", "bg": "#15803D"},
                    {"label": "Parametric", "icon": u"📏", "bg": "#0284C7"}
                ],
                "specs": {
                    "Discipline": disc,
                    "Category": cat,
                    "Source": "Master Library RVT",
                    "Master File": doc_title
                },
                "source_doc_path": doc_path,
                "source_doc_title": doc_title,
                "is_level_master": True,
                "thumbnail": thumb_ref
            }
            catalog_dict[fname_upper] = new_item

    # 3. Extract Wall Types from Document
    wall_types = DB.FilteredElementCollector(doc).OfClass(DB.WallType).ToElements()
    for wt in wall_types:
        try:
            wname = DB.Element.Name.GetValue(wt)
        except Exception:
            wname = getattr(wt, "Name", "")
        if not wname:
            continue

        wname_upper = wname.upper()
        current_doc_family_names.add(wname_upper)

        if wname_upper in catalog_dict:
            ex = catalog_dict[wname_upper]
            ex["category"] = "Walls"
            ex["is_system_family"] = True
            ex["system_type"] = "Wall"
            ex["source_doc_path"] = doc_path
            ex["source_doc_title"] = doc_title
            ex["master_type_name"] = wname
        elif wname.startswith("RYN_WAL_"):
            new_wall = {
                "code": wname,
                "title": wname,
                "discipline": "ARCHITECTURAL",
                "category": "Walls",
                "types": [wname],
                "badges": [
                    {"label": "System Wall", "icon": u"🧱", "bg": "#B45309"},
                    {"label": "Riyan Master", "icon": u"⭐", "bg": "#15803D"}
                ],
                "specs": {
                    "System Family": "Basic Wall",
                    "Category": "Walls",
                    "Master File": doc_title
                },
                "is_system_family": True,
                "system_type": "Wall",
                "is_level_master": True,
                "source_doc_path": doc_path,
                "source_doc_title": doc_title,
                "master_type_name": wname,
                "thumbnail": None
            }
            catalog_dict[wname_upper] = new_wall

    # 4. Zero-Stale-Cache Pruning: If an item belongs to this Master RVT but was deleted by user, remove it!
    final_catalog = []
    for item in catalog_dict.values():
        item_source = item.get("source_doc_title", "")
        c_up = item.get("code", "").upper()
        if item_source and item_source == doc_title:
            if c_up not in current_doc_family_names:
                # Deleted from Master RVT! Prune it!
                continue
        final_catalog.append(item)

    # 5. Save updated catalog to SharePoint and Local Cache
    try:
        os.makedirs(CENTRAL_REPOSITORY, exist_ok=True)
        with codecs.open(os.path.join(CENTRAL_REPOSITORY, "catalog.json"), "w", "utf-8") as f:
            json.dump(final_catalog, f, indent=2)
    except Exception:
        pass

    try:
        os.makedirs(LOCAL_CACHE_DIR, exist_ok=True)
        with codecs.open(os.path.join(LOCAL_CACHE_DIR, "catalog.json"), "w", "utf-8") as f:
            json.dump(final_catalog, f, indent=2)
    except Exception:
        pass

# Trigger hook on doc-saved
try:
    doc_arg = None
    if 'EXEC_PARAMS' in globals() and hasattr(EXEC_PARAMS, 'event_args'):
        doc_arg = getattr(EXEC_PARAMS.event_args, 'Document', None)
    if not doc_arg:
        try:
            from pyrevit import revit
            doc_arg = revit.doc
        except Exception:
            pass
    if doc_arg:
        sync_master_library_on_save(doc_arg)
except Exception:
    pass
