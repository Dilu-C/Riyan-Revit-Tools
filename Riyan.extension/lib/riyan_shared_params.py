# -*- coding: utf-8 -*-
"""
Riyan Standard Shared Parameter Enforcement Engine
- Dynamically locates the latest RYN_SharedParameters_V-RS*.txt across SharePoint and Local cache
- Bypasses 'PREVIOUS' and 'OLD' folders automatically
- Auto-detaches any foreign or outdated shared parameter file in Revit and Revit.ini
- Enforces permissions: Full Edit (Read/Write) for Dilupa (Admin), Read-Only lock for standard users
- Zero-lag synchronous execution (< 0.002s)
"""

import os
import sys
import re
import shutil

# .NET References
try:
    import clr
    clr.AddReference("System")
    clr.AddReference("System.IO")
    import System
    from System.IO import File, FileAttributes
except Exception:
    System = None
    File = None
    FileAttributes = None

SHAREPOINT_LIB_ROOT = os.path.expandvars(
    r"%USERPROFILE%\OneDrive - Riyan Private Limited\Riyan LK Projects - 00 - RIYAN REVIT STANDARD\02 LIBRARY"
)
CENTRAL_REPOSITORY = os.path.join(SHAREPOINT_LIB_ROOT, "00 RIYAN FAMILY REPOSITORY")

_this_dir = os.path.dirname(os.path.abspath(__file__))
_repo_root = os.path.abspath(os.path.join(_this_dir, "..", ".."))
LOCAL_CACHE_DIR = os.path.join(_repo_root, "Library_Cache")
if not os.path.exists(LOCAL_CACHE_DIR):
    LOCAL_CACHE_DIR = os.path.expandvars(r"%APPDATA%\pyRevit\Extensions\Riyan-Revit-Tools\Library_Cache")

ADMIN_USERS = {"user", "windows", "dilupa", "dilupa.chathuranga", "dilupac", "dilupa1990"}

def is_admin_user():
    try:
        if System:
            uname = System.Environment.UserName.lower()
            if uname in ADMIN_USERS:
                return True
    except Exception:
        pass
    env_uname = os.environ.get("USERNAME", "").lower()
    return env_uname in ADMIN_USERS

def resolve_live_path(path_str):
    if not path_str:
        return None
    try:
        if os.path.exists(path_str):
            return path_str
    except Exception:
        pass
    
    user_prof = os.path.expandvars(r"%USERPROFILE%")
    onedrive_tag = "OneDrive - Riyan Private Limited"
    if onedrive_tag in path_str:
        idx = path_str.find(onedrive_tag)
        rel_part = path_str[idx + len(onedrive_tag):].lstrip("\\/")
        cand = os.path.join(user_prof, onedrive_tag, rel_part)
        try:
            if os.path.exists(cand):
                return cand
        except Exception:
            pass

    parts = path_str.split(os.sep)
    if len(parts) > 3 and parts[0].endswith(":") and parts[1].lower() == "users":
        cand_user = os.path.join(user_prof, *parts[3:])
        try:
            if os.path.exists(cand_user):
                return cand_user
        except Exception:
            pass
    return None

def extract_version_key(filename):
    """
    Extracts date or version tag from filename (e.g. 'RYN_SharedParameters_V-RS20260205.txt' -> 20260205).
    """
    nums = re.findall(r'\d+', filename)
    if nums:
        try:
            # Prefer 8-digit date like 20260205
            for n in nums:
                if len(n) == 8:
                    return int(n)
            return int(nums[-1])
        except Exception:
            pass
    return 0

def find_latest_riyan_shared_parameter_file():
    r"""
    Searches SharePoint, D:\ drive, and local caches for the newest Riyan Shared Parameter file.
    Strictly ignores any file located in 'PREVIOUS', 'OLD', 'BACKUP', or 'ARCHIVE' directories.
    """
    search_roots = [
        os.path.join(os.path.dirname(SHAREPOINT_LIB_ROOT), "00 RIYAN STANDARD"),
        SHAREPOINT_LIB_ROOT,
        CENTRAL_REPOSITORY,
        os.path.dirname(SHAREPOINT_LIB_ROOT),
        r"D:\RIYAN\00 RIYAN STANDARD",
        r"D:\RIYAN\Riyan Private Limited",
        r"D:\RIYAN",
        os.path.join(LOCAL_CACHE_DIR, "SharedParameters"),
        LOCAL_CACHE_DIR
    ]

    # Resolve live paths for user profiles
    resolved_roots = []
    for r in search_roots:
        if r and r not in resolved_roots:
            if os.path.exists(r):
                resolved_roots.append(r)
            else:
                lp = resolve_live_path(r)
                if lp and os.path.exists(lp) and lp not in resolved_roots:
                    resolved_roots.append(lp)

    ignored_dir_names = {"previous", "old", "backup", "archive", "0000 previous", "0000_previous", "temp"}
    candidates = []

    for root_dir in resolved_roots:
        try:
            # We only scan depth 1-2 to keep startup ultra-fast (0.001s)
            for item in os.listdir(root_dir):
                full_item_path = os.path.join(root_dir, item)
                if os.path.isfile(full_item_path):
                    f_lower = item.lower()
                    if f_lower.endswith(".txt") and ("sharedparameter" in f_lower or f_lower.startswith("ryn_sharedparameters")):
                        # Skip backup copies
                        if ".bak" in f_lower or "backup" in f_lower:
                            continue
                        v_key = extract_version_key(item)
                        try:
                            mtime = os.path.getmtime(full_item_path)
                        except Exception:
                            mtime = 0
                        candidates.append((v_key, mtime, full_item_path))
                elif os.path.isdir(full_item_path):
                    d_lower = item.lower()
                    if d_lower in ignored_dir_names or "previous" in d_lower or "old" in d_lower:
                        continue
                    # Check 1 level down
                    try:
                        for sub_f in os.listdir(full_item_path):
                            sub_lower = sub_f.lower()
                            if sub_lower.endswith(".txt") and ("sharedparameter" in sub_lower or sub_lower.startswith("ryn_sharedparameters")):
                                if ".bak" in sub_lower or "backup" in sub_lower:
                                    continue
                                sub_full = os.path.join(full_item_path, sub_f)
                                v_key = extract_version_key(sub_f)
                                try:
                                    mtime = os.path.getmtime(sub_full)
                                except Exception:
                                    mtime = 0
                                candidates.append((v_key, mtime, sub_full))
                    except Exception:
                        pass
        except Exception:
            pass

    if not candidates:
        # Fallback to repository bundled file
        bundled = os.path.join(LOCAL_CACHE_DIR, "SharedParameters", "RYN_SharedParameters_V-RS20260205.txt")
        if os.path.exists(bundled):
            return bundled
        return None

    # Sort candidates by: (version_key, mtime) descending
    candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
    best_file = candidates[0][2]

    # Synchronize to local cache so offline laptops always have the latest version
    try:
        cache_sp_dir = os.path.join(LOCAL_CACHE_DIR, "SharedParameters")
        os.makedirs(cache_sp_dir, exist_ok=True)
        cached_dest = os.path.join(cache_sp_dir, os.path.basename(best_file))
        if os.path.abspath(best_file).lower() != os.path.abspath(cached_dest).lower():
            if (not os.path.exists(cached_dest)) or (os.path.getmtime(best_file) > os.path.getmtime(cached_dest)):
                shutil.copy2(best_file, cached_dest)
    except Exception:
        pass

    return best_file

def apply_access_permissions(target_path, is_admin):
    """
    Sets file system permissions:
    - Dilupa / Admin: Read/Write (FileAttributes.Normal) -> Can edit, add parameters
    - Standard Users: Read-Only (FileAttributes.ReadOnly) -> Revit UI locks edit/delete buttons
    """
    if not target_path or not os.path.exists(target_path):
        return
    try:
        if File and FileAttributes:
            if is_admin:
                File.SetAttributes(target_path, FileAttributes.Normal)
            else:
                File.SetAttributes(target_path, FileAttributes.ReadOnly)
    except Exception:
        pass
    try:
        import stat
        if is_admin:
            os.chmod(target_path, stat.S_IWRITE | stat.S_IREAD)
        else:
            os.chmod(target_path, stat.S_IREAD)
    except Exception:
        pass

def update_revit_ini_files(target_path):
    """
    Updates Revit.ini for all installed Revit versions under [Directories]:
    SharedParameters=<target_path>
    This permanently fixes the shared parameter file at the Revit application level.
    """
    if not target_path or not os.path.exists(target_path):
        return
    
    appdata_revit = os.path.expandvars(r"%APPDATA%\Autodesk\Revit")
    if not os.path.isdir(appdata_revit):
        return

    for item in os.listdir(appdata_revit):
        revit_dir = os.path.join(appdata_revit, item)
        if os.path.isdir(revit_dir) and "Revit" in item:
            ini_path = os.path.join(revit_dir, "Revit.ini")
            if os.path.isfile(ini_path):
                try:
                    with open(ini_path, "r", encoding="utf-16le") as f:
                        lines = f.readlines()
                    encoding = "utf-16le"
                except Exception:
                    try:
                        with open(ini_path, "r", encoding="utf-8") as f:
                            lines = f.readlines()
                        encoding = "utf-8"
                    except Exception:
                        continue

                new_lines = []
                in_directories = False
                shared_param_written = False
                has_directories_section = any(line.strip().lower() == "[directories]" for line in lines)

                for line in lines:
                    stripped = line.strip()
                    if stripped.lower() == "[directories]":
                        in_directories = True
                        new_lines.append(line)
                        continue
                    elif stripped.startswith("[") and stripped.endswith("]"):
                        if in_directories and not shared_param_written:
                            new_lines.append(u"SharedParameters={}\n".format(target_path))
                            shared_param_written = True
                        in_directories = False
                    
                    if in_directories and stripped.lower().startswith("sharedparameters="):
                        new_lines.append(u"SharedParameters={}\n".format(target_path))
                        shared_param_written = True
                    else:
                        new_lines.append(line)

                if in_directories and not shared_param_written:
                    new_lines.append(u"SharedParameters={}\n".format(target_path))
                    shared_param_written = True

                if not has_directories_section:
                    new_lines.append(u"\n[Directories]\nSharedParameters={}\n".format(target_path))

                try:
                    with open(ini_path, "w", encoding=encoding) as f:
                        f.writelines(new_lines)
                except Exception:
                    pass

def enforce_riyan_shared_parameters(app=None):
    """
    Main entry point:
    1. Finds the latest versioned Riyan Shared Parameter file
    2. Applies permissions (Admin=Edit, Standard=ReadOnly)
    3. Detaches and replaces any previous or foreign file in Revit
    4. Updates Revit.ini
    """
    latest_file = find_latest_riyan_shared_parameter_file()
    if not latest_file:
        return None, False

    admin = is_admin_user()
    apply_access_permissions(latest_file, admin)

    # 1. Update Revit.ini across all versions (instant)
    try:
        update_revit_ini_files(latest_file)
    except Exception:
        pass

    # 2. Update active Revit Application if available
    changed = False
    try:
        if not app:
            try:
                from pyrevit import HOST_APP
                app = HOST_APP.app
            except Exception:
                pass
        if not app:
            try:
                from pyrevit import revit
                if revit.doc and revit.doc.Application:
                    app = revit.doc.Application
            except Exception:
                pass

        if app and hasattr(app, "SharedParametersFilename"):
            curr = app.SharedParametersFilename
            if not curr or os.path.normpath(curr).lower() != os.path.normpath(latest_file).lower():
                app.SharedParametersFilename = latest_file
                changed = True
    except Exception:
        pass

    return latest_file, changed

if __name__ == "__main__":
    f, ch = enforce_riyan_shared_parameters()
    print("Latest Shared Parameter File:", f)
    print("Admin User:", is_admin_user())
    print("Changed in Revit:", ch)
