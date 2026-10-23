# -*- coding: utf-8 -*-
"""
Generate skills_manifest.json for Riyan Skills Hub
Calculates SHA256 hashes and metadata for all skills in Skills_Hub.
"""

import os
import sys
import json
import hashlib
import io

def get_file_hash(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def parse_frontmatter(md_path):
    frontmatter = {}
    if not os.path.exists(md_path):
        return frontmatter
    try:
        with io.open(md_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        try:
            with io.open(md_path, "r", encoding="latin-1", errors="replace") as f:
                content = f.read()
        except Exception:
            with open(md_path, "r") as f:
                content = f.read()

    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            raw_yaml = parts[1]
            for line in raw_yaml.splitlines():
                line = line.strip()
                if line and ":" in line and not line.startswith("#"):
                    k, v = line.split(":", 1)
                    frontmatter[k.strip()] = v.strip().strip('"').strip("'")
    return frontmatter

def build_manifest():
    hub_dir = os.path.dirname(os.path.abspath(__file__))
    ext_dir = os.path.join(os.path.dirname(hub_dir), "Riyan.extension", "lib")
    if ext_dir not in sys.path:
        sys.path.append(ext_dir)

    try:
        import skill_sentinel
        print("[*] Running Sentinel Peer Conflict & Guardrail Audit before manifest generation...")
        audit = skill_sentinel.audit_all_skills_in_hub(hub_dir)
        if audit.get("status") == "CLASH":
            print("[ERROR] Skills Hub audit detected conflicts! Resolve before publishing:")
            for p in audit.get("peer_to_peer_conflicts", []):
                print("  [PEER CLASH] " + str(p["skill_a"]) + " vs " + str(p["skill_b"]) + " on '" + str(p["topic"]) + "': " + str(p["description"]))
            for c in audit.get("company_rule_violations", []):
                print("  [GUARDRAIL] " + str(c["skill"]) + " violates " + str(c["clash"]["rule_id"]) + ": " + str(c["clash"]["description"]))
            return None
        else:
            print("[OK] Sentinel Audit Passed: 0 Peer Conflicts, 0 Guardrail Violations.")
    except Exception as e:
        print("[WARN] Sentinel check skipped: " + str(e))

    manifest = {
        "hub_version": "1.0.0",
        "generated_at": os.popen("powershell Get-Date -Format s").read().strip() if os.name == "nt" else "",
        "repo_url": "https://raw.githubusercontent.com/Dilu-C/Riyan-Revit-Tools/main/Skills_Hub",
        "rules_url": "https://raw.githubusercontent.com/Dilu-C/Riyan-Revit-Tools/main/Rules_Hub",
        "skills": {},
        "rules": {}
    }

    for item in sorted(os.listdir(hub_dir)):
        skill_dir = os.path.join(hub_dir, item)
        if os.path.isdir(skill_dir) and not item.startswith("."):
            skill_md = os.path.join(skill_dir, "SKILL.md")
            if os.path.exists(skill_md):
                fm = parse_frontmatter(skill_md)
                sha = get_file_hash(skill_md)
                manifest["skills"][item] = {
                    "name": fm.get("name", item),
                    "description": fm.get("description", ""),
                    "author": fm.get("author", "Riyan BIM Team"),
                    "office": fm.get("office", "Sri Lanka & Maldives"),
                    "discipline": fm.get("discipline", "General"),
                    "version": fm.get("version", "1.0.0"),
                    "sha256": sha,
                    "rel_path": str(item) + "/SKILL.md",
                    "size_bytes": os.path.getsize(skill_md)
                }

    # Index Rules_Hub
    rules_dir = os.path.join(os.path.dirname(hub_dir), "Rules_Hub")
    if os.path.exists(rules_dir):
        for r_file in sorted(os.listdir(rules_dir)):
            if r_file.endswith(".md"):
                r_path = os.path.join(rules_dir, r_file)
                r_sha = get_file_hash(r_path)
                manifest["rules"][r_file] = {
                    "filename": r_file,
                    "sha256": r_sha,
                    "rel_path": "Rules_Hub/" + r_file,
                    "size_bytes": os.path.getsize(r_path)
                }

    manifest_path = os.path.join(hub_dir, "skills_manifest.json")
    try:
        with io.open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
    except Exception:
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

    print("[OK] Generated skills_manifest.json with " + str(len(manifest["skills"])) + " skills and " + str(len(manifest["rules"])) + " rules.")
    return manifest_path

if __name__ == "__main__":
    build_manifest()
