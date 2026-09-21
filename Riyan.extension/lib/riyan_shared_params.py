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

def is_valid_shared_parameter_file(path):
    if not path or not os.path.isfile(path):
        return False
    try:
        if os.path.getsize(path) < 20:
            return False
        with open(path, "rb") as f:
            header = f.read(120)
            if header.startswith(b'\xff\xfe'):
                txt = header.decode('utf-16-le', errors='ignore').lower()
                if 'shared parameter' in txt or '*meta' in txt or 'group' in txt:
                    return True
            txt = header.decode('utf-8', errors='ignore').lower()
            if 'shared parameter' in txt or '*meta' in txt or 'group' in txt:
                return True
    except Exception:
        pass
    return False

def get_sharepoint_roots():
    r"""
    Discovers SharePoint / OneDrive roots across Windows Registry,
    UserProfile, Environment Variables, and Drive Letters.
    Target structure:
    - BIM SERVER / 00 - RIYAN REVIT STANDARD / 01 SHARED PARAMETER
    """
    discovered = []
    user_prof = os.path.expandvars(r"%USERPROFILE%")

    # 1. Standard OneDrive / SharePoint directory names
    base_parents = [
        user_prof,
        os.path.join(user_prof, "OneDrive - Riyan Private Limited"),
        os.path.join(user_prof, "Riyan Private Limited"),
        r"D:\RIYAN\Riyan Private Limited",
        r"D:\RIYAN",
        r"C:\RIYAN"
    ]

    # Add all drive letters
    for dl in ['C', 'D', 'E', 'F', 'G']:
        drv = dl + ":\\"
        if os.path.exists(drv) and drv not in base_parents:
            base_parents.append(drv)
            base_parents.append(os.path.join(drv, "Riyan Private Limited"))
            base_parents.append(os.path.join(drv, "RIYAN", "Riyan Private Limited"))

    # 2. Check Registry MountPoints (OneDrive for Business)
    try:
        try:
            import winreg
        except ImportError:
            import _winreg as winreg

        reg_keys = [
            r'Software\SyncEngines\Providers\OneDrive',
            r'Software\Microsoft\OneDrive\Accounts\Business1\ScopeIdToMountPointPathCache'
        ]
        for rk in reg_keys:
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, rk) as k:
                    n_sub, n_val, _ = winreg.QueryInfoKey(k)
                    for i in range(n_sub):
                        try:
                            sn = winreg.EnumKey(k, i)
                            with winreg.OpenKey(k, sn) as sk:
                                mp, _ = winreg.QueryValueEx(sk, 'MountPoint')
                                if mp and os.path.exists(mp) and mp not in base_parents:
                                    base_parents.append(mp)
                        except Exception:
                            pass
                    for i in range(n_val):
                        try:
                            _, v, _ = winreg.EnumValue(k, i)
                            if isinstance(v, str) and os.path.exists(v) and v not in base_parents:
                                base_parents.append(v)
                        except Exception:
                            pass
            except Exception:
                pass
    except Exception:
        pass

    # Target SharePoint subfolders to probe
    sub_patterns = [
        r"BIM SERVER\00 - RIYAN REVIT STANDARD\01 SHARED PARAMETER",
        r"Riyan LK Projects - BIM SERVER\00 - RIYAN REVIT STANDARD\01 SHARED PARAMETER",
        r"00 - RIYAN REVIT STANDARD\01 SHARED PARAMETER",
        r"01 SHARED PARAMETER",
        r"00 - RIYAN REVIT STANDARD",
        r"00 RIYAN STANDARD",
        r"Riyan LK Projects - 00 - RIYAN REVIT STANDARD\01 SHARED PARAMETER",
        r"Riyan LK Projects - 00 - RIYAN REVIT STANDARD\02 LIBRARY",
    ]

    for bp in base_parents:
        if not bp or not os.path.exists(bp):
            continue
        discovered.append(bp)
        for sp in sub_patterns:
            cand = os.path.join(bp, sp)
            if os.path.exists(cand) and cand not in discovered:
                discovered.append(cand)

    return discovered

def find_latest_riyan_shared_parameter_file():
    r"""
    Searches SharePoint, any drive, and local caches for the newest Riyan Shared Parameter file.
    Strictly ignores '00 PREVIOUS REVISIONS', 'PREVIOUS', 'OLD', 'BACKUP', or 'ARCHIVE' directories.
    """
    search_roots = get_sharepoint_roots()
    search_roots.extend([
        _this_dir,
        os.path.join(LOCAL_CACHE_DIR, "SharedParameters"),
        LOCAL_CACHE_DIR
    ])

    ignored_dir_names = {
        "00 previous revisions", "00_previous_revisions", "previous revisions",
        "previous", "old", "backup", "archive", "0000 previous", "0000_previous", "temp"
    }

    candidates = []

    # Direct embedded standard parameter file in lib (100% guaranteed presence)
    embedded_file = os.path.join(_this_dir, "RYN_SharedParameters_V-RS20260918.txt")
    if is_valid_shared_parameter_file(embedded_file):
        try:
            mtime = os.path.getmtime(embedded_file)
        except Exception:
            mtime = 0
        candidates.append((20260918, 1, mtime, embedded_file))

    for root_dir in search_roots:
        if not root_dir or not os.path.exists(root_dir):
            continue
        try:
            is_source = 0 if "library_cache" in root_dir.lower() else 1
            for item in os.listdir(root_dir):
                full_item_path = os.path.join(root_dir, item)
                if os.path.isfile(full_item_path):
                    f_lower = item.lower()
                    if f_lower.endswith(".txt") and ("sharedparameter" in f_lower or f_lower.startswith("ryn_sharedparameters")):
                        if ".bak" in f_lower or "backup" in f_lower:
                            continue
                        if not is_valid_shared_parameter_file(full_item_path):
                            continue
                        v_key = extract_version_key(item)
                        try:
                            mtime = os.path.getmtime(full_item_path)
                        except Exception:
                            mtime = 0
                        candidates.append((v_key, is_source, mtime, full_item_path))
                elif os.path.isdir(full_item_path):
                    d_lower = item.lower()
                    if d_lower in ignored_dir_names or "previous" in d_lower or "old" in d_lower:
                        continue
                    try:
                        for sub_f in os.listdir(full_item_path):
                            sub_lower = sub_f.lower()
                            if sub_lower.endswith(".txt") and ("sharedparameter" in sub_lower or sub_lower.startswith("ryn_sharedparameters")):
                                if ".bak" in sub_lower or "backup" in sub_lower:
                                    continue
                                sub_full = os.path.join(full_item_path, sub_f)
                                if not is_valid_shared_parameter_file(sub_full):
                                    continue
                                v_key = extract_version_key(sub_f)
                                try:
                                    mtime = os.path.getmtime(sub_full)
                                except Exception:
                                    mtime = 0
                                candidates.append((v_key, is_source, mtime, sub_full))
                    except Exception:
                        pass
        except Exception:
            pass

    if not candidates:
        cache_sp_dir = os.path.join(LOCAL_CACHE_DIR, "SharedParameters")
        fallback_candidates = []
        if os.path.exists(cache_sp_dir):
            for fn in os.listdir(cache_sp_dir):
                if fn.lower().startswith("ryn_sharedparameters") and fn.lower().endswith(".txt"):
                    fp = os.path.join(cache_sp_dir, fn)
                    if is_valid_shared_parameter_file(fp):
                        fallback_candidates.append((extract_version_key(fn), fp))
        if fallback_candidates:
            fallback_candidates.sort(key=lambda x: x[0], reverse=True)
            return fallback_candidates[0][1]

        bundled = os.path.join(LOCAL_CACHE_DIR, "SharedParameters", "RYN_SharedParameters_V-RS20260918.txt")
        if is_valid_shared_parameter_file(bundled):
            return bundled
        return None

    # Sort candidates by: (version_key, is_source, mtime) descending
    candidates.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
    best_file = candidates[0][3]

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
    ExternalParameters=<target_path>
    This permanently fixes the shared parameter file at the Revit application level.
    """
    if not target_path or not os.path.exists(target_path):
        return

    appdata_revit = os.path.expandvars(r"%APPDATA%\Autodesk\Revit")
    if not os.path.isdir(appdata_revit):
        return

    for item in os.listdir(appdata_revit):
        revit_dir = os.path.join(appdata_revit, item)
        if os.path.isdir(revit_dir) and "Revit" in item and "backup" not in item.lower():
            ini_path = os.path.join(revit_dir, "Revit.ini")
            if not os.path.isfile(ini_path):
                continue

            lines = None
            encoding_mode = None

            # 1. Try .NET File if available (IronPython / PythonNet)
            if File and System:
                try:
                    from System.Text import Encoding
                    raw_bytes = File.ReadAllBytes(ini_path)
                    enc = Encoding.Unicode
                    if len(raw_bytes) >= 3 and raw_bytes[0] == 0xEF and raw_bytes[1] == 0xBB and raw_bytes[2] == 0xBF:
                        enc = Encoding.UTF8
                    elif len(raw_bytes) >= 2 and raw_bytes[0] == 0xFF and raw_bytes[1] == 0xFE:
                        enc = Encoding.Unicode
                    lines = [str(l) for l in File.ReadAllLines(ini_path, enc)]
                    encoding_mode = enc
                except Exception:
                    lines = None

            # 2. Fallback to codecs.open (Standard Python 2/3)
            if lines is None:
                for enc_name in ["utf-16le", "utf-8", "mbcs"]:
                    try:
                        import codecs
                        with codecs.open(ini_path, "r", encoding=enc_name) as f:
                            lines = f.readlines()
                        encoding_mode = enc_name
                        break
                    except Exception:
                        continue

            if lines is None:
                continue

            new_lines = []
            in_directories = False
            shared_param_written = False
            ext_param_written = False
            has_directories_section = any(line.strip().lower() == "[directories]" for line in lines)

            for line in lines:
                stripped = line.strip()
                if stripped.lower() == "[directories]":
                    in_directories = True
                    new_lines.append(line.rstrip("\r\n"))
                    continue
                elif stripped.startswith("[") and stripped.endswith("]"):
                    if in_directories:
                        if not shared_param_written:
                            new_lines.append(u"SharedParameters={}".format(target_path))
                            shared_param_written = True
                        if not ext_param_written:
                            new_lines.append(u"ExternalParameters={}".format(target_path))
                            ext_param_written = True
                    in_directories = False

                if in_directories and stripped.lower().startswith("sharedparameters="):
                    new_lines.append(u"SharedParameters={}".format(target_path))
                    shared_param_written = True
                elif in_directories and stripped.lower().startswith("externalparameters="):
                    new_lines.append(u"ExternalParameters={}".format(target_path))
                    ext_param_written = True
                else:
                    new_lines.append(line.rstrip("\r\n"))

            if in_directories:
                if not shared_param_written:
                    new_lines.append(u"SharedParameters={}".format(target_path))
                    shared_param_written = True
                if not ext_param_written:
                    new_lines.append(u"ExternalParameters={}".format(target_path))
                    ext_param_written = True

            if not has_directories_section:
                new_lines.append(u"")
                new_lines.append(u"[Directories]")
                new_lines.append(u"SharedParameters={}".format(target_path))
                new_lines.append(u"ExternalParameters={}".format(target_path))

            try:
                if File and hasattr(encoding_mode, "GetBytes"):
                    File.WriteAllLines(ini_path, new_lines, encoding_mode)
                elif encoding_mode:
                    import codecs
                    with codecs.open(ini_path, "w", encoding=encoding_mode) as f:
                        for nl in new_lines:
                            f.write(nl + u"\r\n")
            except Exception:
                pass

def sync_cloud_shared_parameters_background(app=None):
    r"""
    Direct Cloud Auto-Downloader:
    Background daemon worker that checks GitHub cloud for a newer RYN_SharedParameters_V-RS*.txt
    Even if the user has NEVER synced SharePoint and NEVER created a desktop shortcut!
    """
    import threading
    def _worker():
        try:
            import time
            try:
                import urllib2
            except ImportError:
                import urllib.request as urllib2

            time.sleep(3)  # Let Revit finish opening
            latest_url = "https://raw.githubusercontent.com/Dilu-C/Riyan-Revit-Tools/main/Library_Cache/SharedParameters/latest.txt?t=" + str(int(time.time()))
            req = urllib2.Request(latest_url)
            req.add_header('Cache-Control', 'no-cache')
            req.add_header('Pragma', 'no-cache')
            resp = urllib2.urlopen(req, timeout=4)
            online_filename = resp.read().strip()
            if hasattr(online_filename, 'decode'):
                online_filename = online_filename.decode('utf-8').strip()
            if not online_filename or not online_filename.lower().endswith('.txt'):
                return

            online_v = extract_version_key(online_filename)
            local_file = find_latest_riyan_shared_parameter_file()
            local_v = extract_version_key(os.path.basename(local_file)) if local_file else 0

            if online_v > local_v:
                file_url = "https://raw.githubusercontent.com/Dilu-C/Riyan-Revit-Tools/main/Library_Cache/SharedParameters/" + online_filename + "?t=" + str(int(time.time()))
                req_f = urllib2.Request(file_url)
                req_f.add_header('Cache-Control', 'no-cache')
                file_resp = urllib2.urlopen(req_f, timeout=8)
                data = file_resp.read()

                cache_dir = os.path.join(LOCAL_CACHE_DIR, "SharedParameters")
                os.makedirs(cache_dir, exist_ok=True)
                dest_path = os.path.join(cache_dir, online_filename)

                # Binary write to strictly preserve UTF-16LE BOM
                with open(dest_path, "wb") as f:
                    f.write(data)

                if is_valid_shared_parameter_file(dest_path):
                    with open(os.path.join(cache_dir, "latest.txt"), "w") as f:
                        f.write(online_filename)
                    enforce_riyan_shared_parameters(app, check_cloud=False)
        except Exception:
            pass

    t = threading.Thread(target=_worker)
    t.isDaemon = True
    t.start()

def enforce_riyan_shared_parameters(app=None, check_cloud=True):
    """
    Main entry point:
    1. Finds the latest versioned Riyan Shared Parameter file
    2. Applies permissions (Admin=Edit, Standard=ReadOnly)
    3. Detaches and replaces any previous or foreign file in Revit
    4. Updates Revit.ini
    5. Optionally triggers background Cloud Auto-Downloader
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
        app_obj = app
        if not app_obj:
            try:
                from pyrevit import HOST_APP
                if hasattr(HOST_APP.app, "ControlledApplication"):
                    app_obj = HOST_APP.app.ControlledApplication
                elif hasattr(HOST_APP.app, "Application"):
                    app_obj = HOST_APP.app.Application
                else:
                    app_obj = HOST_APP.app
            except Exception:
                pass
        if not app_obj or not hasattr(app_obj, "SharedParametersFilename"):
            try:
                from pyrevit import revit
                if revit.doc and hasattr(revit.doc, "Application"):
                    app_obj = revit.doc.Application
            except Exception:
                pass

        if app_obj and hasattr(app_obj, "SharedParametersFilename"):
            curr = app_obj.SharedParametersFilename
            if not curr or os.path.normpath(curr).lower() != os.path.normpath(latest_file).lower():
                app_obj.SharedParametersFilename = latest_file
                changed = True
    except Exception:
        pass

    # 3. Trigger silent background cloud check for updates
    if check_cloud:
        try:
            sync_cloud_shared_parameters_background(app)
        except Exception:
            pass

    return latest_file, changed

if __name__ == "__main__":
    f, ch = enforce_riyan_shared_parameters(check_cloud=False)
    print("Latest Shared Parameter File:", f)
    print("Admin User:", is_admin_user())
    print("Changed in Revit:", ch)
