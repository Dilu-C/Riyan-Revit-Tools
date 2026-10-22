# -*- coding: utf-8 -*-
"""
skills_sync.py - Real-Time Online Antigravity Skills Fleet Engine for Riyan Revit Tools
Multi-Office Support: Sri Lanka & Maldives
Compatibility: IronPython 2.7, CPython 3.8-3.13+, Revit 2021-2027+, Standalone Daemon
Features:
- Online GitHub Raw Manifest auto-polling (Zero-Touch, no batch file required)
- SHA256 / Timestamp delta sync: only fetches updated files
- Background heartbeat daemon (polls every 5 minutes while software is running)
- Silent fail-safe: zero crash, zero popups on network loss
"""

import os
import sys
import json
import time
import shutil
import threading

# Compatibility imports for urllib across IronPython 2.7 and Python 3
try:
    import urllib2
    from urllib2 import urlopen, Request
except ImportError:
    import urllib.request as urllib2
    from urllib.request import urlopen, Request

try:
    import hashlib
    HAS_HASH = True
except ImportError:
    HAS_HASH = False

ONLINE_REPO_BASE = "https://raw.githubusercontent.com/Dilu-C/Riyan-Revit-Tools/main/Skills_Hub"
ONLINE_MANIFEST_URL = ONLINE_REPO_BASE + "/skills_manifest.json"

_HEARTBEAT_THREAD = None
_STOP_HEARTBEAT = False

def get_sentinel():
    """Dynamically imports skill_sentinel if available."""
    try:
        import skill_sentinel
        return skill_sentinel
    except ImportError:
        try:
            lib_dir = os.path.dirname(__file__)
            if lib_dir not in sys.path:
                sys.path.append(lib_dir)
            import skill_sentinel
            return skill_sentinel
        except Exception:
            return None

def get_target_skills_dirs():
    """Returns all Antigravity skill directories on the local machine (global and project workspaces)."""
    user_profile = os.environ.get('USERPROFILE', os.path.expanduser('~'))
    gemini_dir = os.path.join(user_profile, '.gemini')
    if not os.path.exists(gemini_dir):
        # Auto-create if Antigravity config path exists
        try:
            os.makedirs(os.path.join(gemini_dir, 'config', 'skills'))
        except Exception:
            pass

    dirs = [
        os.path.join(gemini_dir, 'config', 'skills'),
        os.path.join(gemini_dir, 'antigravity', 'skills')
    ]

    # Auto-discover any active Antigravity project workspaces (.agents/skills)
    search_roots = [
        os.path.join(user_profile, 'Desktop'),
        os.path.join(user_profile, 'Documents')
    ]
    for s_root in search_roots:
        if not os.path.exists(s_root):
            continue
        try:
            for root, subdirs, files in os.walk(s_root):
                if '.agents' in subdirs:
                    project_skills = os.path.join(root, '.agents', 'skills')
                    if os.path.exists(project_skills) and project_skills not in dirs:
                        dirs.append(project_skills)
                depth = root[len(s_root):].count(os.sep)
                if depth >= 3:
                    subdirs[:] = []
        except Exception:
            pass

    return dirs

def get_corporate_fleet_dir():
    """Locates the shared Riyan Corporate OneDrive / SharePoint Skills Fleet directory."""
    user_profile = os.environ.get('USERPROFILE', os.path.expanduser('~'))
    candidates = [
        os.path.join(user_profile, 'OneDrive - Riyan Private Limited', 'Riyan LK Projects - 00 - RIYAN REVIT STANDARD', '04 AUTOMATION', 'RIYAN_SKILLS_FLEET'),
        os.path.join(user_profile, 'Riyan Private Limited', 'Riyan LK Projects - 00 - RIYAN REVIT STANDARD', '04 AUTOMATION', 'RIYAN_SKILLS_FLEET'),
        r'D:\RIYAN\Riyan Private Limited\Riyan LK Projects - 00 - RIYAN REVIT STANDARD\04 AUTOMATION\RIYAN_SKILLS_FLEET'
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    # Try parent auto-creation if standard folder exists
    base_candidates = [
        os.path.join(user_profile, 'OneDrive - Riyan Private Limited', 'Riyan LK Projects - 00 - RIYAN REVIT STANDARD', '04 AUTOMATION'),
        os.path.join(user_profile, 'Riyan Private Limited', 'Riyan LK Projects - 00 - RIYAN REVIT STANDARD', '04 AUTOMATION')
    ]
    for b in base_candidates:
        if os.path.exists(b):
            target = os.path.join(b, 'RIYAN_SKILLS_FLEET')
            try:
                os.makedirs(target)
                return target
            except Exception:
                pass
    return None

def get_local_skills_hub_dir():
    """Locates the local fallback Skills_Hub in Riyan-Revit-Tools repository root."""
    current_lib = os.path.dirname(__file__)
    ext_dir = os.path.dirname(current_lib)
    repo_root = os.path.dirname(ext_dir)
    hub_dir = os.path.join(repo_root, 'Skills_Hub')
    if os.path.exists(hub_dir):
        return hub_dir
    return None

def compute_sha256(filepath):
    """Computes SHA256 of a local file."""
    if not HAS_HASH or not os.path.exists(filepath):
        return None
    try:
        h = hashlib.sha256()
        with open(filepath, 'rb') as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None

def fetch_url_text(url, timeout=6):
    """Fetches text content from a remote URL with cache-busting."""
    try:
        cache_buster = "?_t=" + str(int(time.time()))
        req = Request(url + cache_buster)
        req.add_header('User-Agent', 'Riyan-Skills-Fleet-Engine/1.0')
        req.add_header('Cache-Control', 'no-cache')
        req.add_header('Pragma', 'no-cache')
        response = urlopen(req, timeout=timeout)
        data = response.read()
        if hasattr(data, 'decode'):
            return data.decode('utf-8', errors='replace')
        return str(data)
    except Exception:
        return None

def publish_local_skills_to_fleet():
    """
    Bidirectional Uplink:
    Detects any locally created/modified skill on this PC (by any user or project)
    and publishes it to the Corporate Fleet so every other PC receives it.
    """
    fleet_dir = get_corporate_fleet_dir()
    if not fleet_dir or not os.path.exists(fleet_dir):
        return False

    target_dirs = get_target_skills_dirs()
    sentinel = get_sentinel()
    published = 0

    for local_dir in target_dirs:
        if not os.path.exists(local_dir):
            continue
        for item in os.listdir(local_dir):
            skill_path = os.path.join(local_dir, item)
            if not os.path.isdir(skill_path) or item.startswith('.'):
                continue
            skill_md = os.path.join(skill_path, 'SKILL.md')
            if not os.path.exists(skill_md):
                continue

            fleet_skill_dir = os.path.join(fleet_dir, item)
            fleet_skill_md = os.path.join(fleet_skill_dir, 'SKILL.md')

            needs_push = False
            if not os.path.exists(fleet_skill_md):
                needs_push = True
            else:
                try:
                    if os.path.getmtime(skill_md) > (os.path.getmtime(fleet_skill_md) + 2):
                        needs_push = True
                except Exception:
                    pass

            if needs_push:
                try:
                    with open(skill_md, 'r', encoding='utf-8') as sf:
                        content = sf.read()
                except Exception:
                    with open(skill_md, 'r', encoding='latin-1', errors='replace') as sf:
                        content = sf.read()

                if sentinel:
                    is_safe, clash_info = sentinel.audit_incoming_skill(item, content, target_dirs)
                    if not is_safe:
                        print(f"[SENTINEL] Refused to publish conflicting skill '{item}' to Fleet!")
                        continue

                try:
                    if not os.path.exists(fleet_skill_dir):
                        os.makedirs(fleet_skill_dir)
                    for f in os.listdir(skill_path):
                        src_f = os.path.join(skill_path, f)
                        dst_f = os.path.join(fleet_skill_dir, f)
                        if os.path.isfile(src_f):
                            shutil.copy2(src_f, dst_f)
                    published += 1
                    print(f"[FLEET UPLINK] Successfully published '{item}' to Corporate Fleet!")
                except Exception as ex:
                    print(f"[FLEET ERROR] Could not publish '{item}': {ex}")

    return published > 0

def pull_skills_from_fleet():
    """
    Corporate Fleet Downlink:
    Silently syncs any skills published by other PCs in the office via OneDrive / Corporate Share.
    """
    fleet_dir = get_corporate_fleet_dir()
    if not fleet_dir or not os.path.exists(fleet_dir):
        return False

    target_dirs = get_target_skills_dirs()
    sentinel = get_sentinel()
    pulled = 0

    for item in os.listdir(fleet_dir):
        fleet_skill = os.path.join(fleet_dir, item)
        if not os.path.isdir(fleet_skill) or item.startswith('.'):
            continue
        fleet_skill_md = os.path.join(fleet_skill, 'SKILL.md')
        if not os.path.exists(fleet_skill_md):
            continue

        for t_dir in target_dirs:
            local_skill_dir = os.path.join(t_dir, item)
            local_skill_md = os.path.join(local_skill_dir, 'SKILL.md')

            needs_copy = False
            if not os.path.exists(local_skill_md):
                needs_copy = True
            else:
                try:
                    if os.path.getmtime(fleet_skill_md) > (os.path.getmtime(local_skill_md) + 2):
                        needs_copy = True
                except Exception:
                    pass

            if needs_copy:
                try:
                    with open(fleet_skill_md, 'r', encoding='utf-8') as sf:
                        content = sf.read()
                except Exception:
                    with open(fleet_skill_md, 'r', encoding='latin-1', errors='replace') as sf:
                        content = sf.read()

                if sentinel:
                    is_safe, clash_info = sentinel.audit_incoming_skill(item, content, target_dirs)
                    if not is_safe:
                        print(f"[SENTINEL] Blocked incoming conflicting skill '{item}' from Fleet!")
                        continue

                try:
                    if not os.path.exists(local_skill_dir):
                        os.makedirs(local_skill_dir)
                    for f in os.listdir(fleet_skill):
                        src_f = os.path.join(fleet_skill, f)
                        dst_f = os.path.join(local_skill_dir, f)
                        if os.path.isfile(src_f):
                            shutil.copy2(src_f, dst_f)
                    pulled += 1
                except Exception:
                    pass

    return pulled > 0

def sync_approved_skills():
    """
    Executes a complete bidirectional single-pass delta sync:
    1. Uplink: Publishes locally created/modified skills to Corporate Fleet (OneDrive).
    2. Corporate Downlink: Pulls skills published by other PCs from Corporate Fleet.
    3. Internet Downlink: Pulls approved skills from central GitHub manifest.
    4. Local Fallback: Pulls from local extension Skills_Hub if offline.
    """
    target_dirs = get_target_skills_dirs()
    if not target_dirs:
        return False

    for t_dir in target_dirs:
        if not os.path.exists(t_dir):
            try:
                os.makedirs(t_dir)
            except Exception:
                pass

    # STEP 1: Corporate Fleet Uplink (Publish local skills)
    try:
        publish_local_skills_to_fleet()
    except Exception:
        pass

    # STEP 2: Corporate Fleet Downlink (Pull skills from other PCs via OneDrive)
    try:
        pull_skills_from_fleet()
    except Exception:
        pass

    # 1. Try Online Manifest
    manifest_json_str = fetch_url_text(ONLINE_MANIFEST_URL, timeout=5)
    manifest = None
    if manifest_json_str:
        try:
            manifest = json.loads(manifest_json_str)
        except Exception:
            manifest = None

    updated_count = 0

    if manifest and "skills" in manifest:
        # Online Sync Mode
        base_url = manifest.get("repo_url", ONLINE_REPO_BASE)
        for skill_key, skill_info in manifest["skills"].items():
            rel_path = skill_info.get("rel_path", skill_key + "/SKILL.md")
            remote_sha = skill_info.get("sha256")
            remote_file_url = base_url + "/" + rel_path

            for target_skills_dir in target_dirs:
                dest_skill_dir = os.path.join(target_skills_dir, skill_key)
                dest_skill_md = os.path.join(dest_skill_dir, "SKILL.md")

                needs_download = False
                if not os.path.exists(dest_skill_md):
                    needs_download = True
                elif remote_sha:
                    local_sha = compute_sha256(dest_skill_md)
                    if local_sha and local_sha != remote_sha:
                        needs_download = True

                if needs_download:
                    content = fetch_url_text(remote_file_url, timeout=7)
                    if content:
                        sentinel = get_sentinel()
                        if sentinel:
                            is_safe, clash_info = sentinel.audit_incoming_skill(skill_key, content, target_dirs)
                            if not is_safe:
                                print(f"[SENTINEL] Blocked conflicting skill '{skill_key}' from syncing!")
                                continue
                        try:
                            if not os.path.exists(dest_skill_dir):
                                os.makedirs(dest_skill_dir)
                            with open(dest_skill_md, "w") as f:
                                f.write(content.encode("utf-8") if sys.version_info[0] == 2 else content)
                            updated_count += 1
                        except Exception:
                            pass
        return True

    # 2. Local Fallback Mode (Offline)
    local_hub = get_local_skills_hub_dir()
    if local_hub and os.path.exists(local_hub):
        for item in os.listdir(local_hub):
            src_skill = os.path.join(local_hub, item)
            if os.path.isdir(src_skill) and not item.startswith('.'):
                src_skill_md = os.path.join(src_skill, 'SKILL.md')
                if not os.path.exists(src_skill_md):
                    continue

                for target_skills_dir in target_dirs:
                    dest_skill = os.path.join(target_skills_dir, item)
                    dest_skill_md = os.path.join(dest_skill, 'SKILL.md')

                    needs_copy = False
                    if not os.path.exists(dest_skill_md):
                        needs_copy = True
                    else:
                        try:
                            if os.path.getmtime(src_skill_md) > os.path.getmtime(dest_skill_md):
                                needs_copy = True
                        except Exception:
                            pass

                    if needs_copy:
                        sentinel = get_sentinel()
                        if sentinel:
                            try:
                                with open(src_skill_md, 'r', encoding='utf-8') as sf:
                                    s_content = sf.read()
                                is_safe, clash_info = sentinel.audit_incoming_skill(item, s_content, target_dirs)
                                if not is_safe:
                                    print(f"[SENTINEL] Blocked conflicting skill '{item}' from local sync!")
                                    continue
                            except Exception:
                                pass
                        try:
                            if not os.path.exists(dest_skill):
                                os.makedirs(dest_skill)
                            for f in os.listdir(src_skill):
                                s_file = os.path.join(src_skill, f)
                                d_file = os.path.join(dest_skill, f)
                                if os.path.isfile(s_file):
                                    shutil.copy2(s_file, d_file)
                        except Exception:
                            pass
        return True

    return False

def start_heartbeat(interval_seconds=300):
    """
    Launches a background daemon thread that periodically checks for skill updates.
    Runs silently every 5 minutes (default).
    Ensures that when Dilu updates a skill at 12:00 PM, all running PCs sync by 12:05 PM
    without closing or restarting Revit/AutoCAD/Navisworks!
    """
    global _HEARTBEAT_THREAD, _STOP_HEARTBEAT
    if _HEARTBEAT_THREAD and _HEARTBEAT_THREAD.is_alive():
        return

    _STOP_HEARTBEAT = False

    def _worker():
        # First immediate sync on software start
        try:
            sync_approved_skills()
        except Exception:
            pass

        # Periodic loop
        while not _STOP_HEARTBEAT:
            try:
                time.sleep(interval_seconds)
                sync_approved_skills()
            except Exception:
                pass

    _HEARTBEAT_THREAD = threading.Thread(target=_worker)
    _HEARTBEAT_THREAD.isDaemon = True
    _HEARTBEAT_THREAD.name = "RiyanSkillsFleetHeartbeat"
    _HEARTBEAT_THREAD.start()

def stop_heartbeat():
    global _STOP_HEARTBEAT
    _STOP_HEARTBEAT = True

if __name__ == "__main__":
    print("[*] Running standalone manual Skills Fleet Sync...")
    res = sync_approved_skills()
    print("[OK] Sync Completed. Status: " + str(res))
