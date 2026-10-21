# -*- coding: utf-8 -*-
"""
skills_sync.py - Silent Background Antigravity Skills Sync for Riyan Revit Tools
Compatible with IronPython 2.7, CPython 3, Revit 2021-2027+
Zero-Crash & Silent Guardrail Engine
"""

import os
import sys
import shutil

def get_user_antigravity_dir():
    """Locate local Antigravity directory in user profile."""
    user_profile = os.environ.get('USERPROFILE', os.path.expanduser('~'))
    ag_dir = os.path.join(user_profile, '.gemini', 'antigravity')
    if os.path.exists(ag_dir):
        return ag_dir
    return None

def get_skills_hub_dir():
    """Locate Skills_Hub in Riyan-Revit-Tools repository root."""
    current_lib = os.path.dirname(__file__)                     # Riyan.extension/lib
    ext_dir = os.path.dirname(current_lib)                      # Riyan.extension
    repo_root = os.path.dirname(ext_dir)                        # Riyan-Revit-Tools root
    
    hub_dir = os.path.join(repo_root, 'Skills_Hub')
    if os.path.exists(hub_dir):
        return hub_dir
    return None

def sync_approved_skills():
    """
    Synchronizes approved company skills from Skills_Hub into local Antigravity skills.
    Runs silently. If Antigravity is not installed, exits immediately.
    """
    try:
        ag_dir = get_user_antigravity_dir()
        if not ag_dir:
            # Antigravity is not installed on this PC. Silent exit.
            return False

        hub_dir = get_skills_hub_dir()
        if not hub_dir:
            return False

        target_skills_dir = os.path.join(ag_dir, 'skills')
        if not os.path.exists(target_skills_dir):
            try:
                os.makedirs(target_skills_dir)
            except Exception:
                pass

        # Iterate through approved skills in Skills_Hub
        for item in os.listdir(hub_dir):
            src_skill = os.path.join(hub_dir, item)
            if os.path.isdir(src_skill) and not item.startswith('.'):
                dest_skill = os.path.join(target_skills_dir, item)
                
                # Check if skill needs updating
                src_skill_md = os.path.join(src_skill, 'SKILL.md')
                dest_skill_md = os.path.join(dest_skill, 'SKILL.md')
                
                needs_copy = False
                if not os.path.exists(dest_skill_md):
                    needs_copy = True
                else:
                    try:
                        # If hub version is newer, update
                        if os.path.getmtime(src_skill_md) > os.path.getmtime(dest_skill_md):
                            needs_copy = True
                    except Exception:
                        pass

                if needs_copy:
                    if not os.path.exists(dest_skill):
                        try:
                            os.makedirs(dest_skill)
                        except Exception:
                            pass
                    
                    # Copy all files in skill directory
                    for f in os.listdir(src_skill):
                        s_file = os.path.join(src_skill, f)
                        d_file = os.path.join(dest_skill, f)
                        if os.path.isfile(s_file):
                            try:
                                shutil.copy2(s_file, d_file)
                            except Exception:
                                pass
        return True
    except Exception:
        # Complete fail-safe guardrail: never throw or block Revit startup
        return False
