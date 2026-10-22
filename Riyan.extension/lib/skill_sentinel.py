# -*- coding: utf-8 -*-
"""
Skill Sentinel - Automated Antigravity Skills Conflict & Clash Detection Engine
Maintained by Dilu | Riyan BIM Automation Suite
Multi-Office Support: Sri Lanka & Maldives

Auditing Scope:
1. Core Company Guardrail Rules (CAD Zero Deletion, Plan X/Y Invariants, Theme, Security)
2. Peer-to-Peer Cross-Skill Conflict Audit (All-vs-All Skill Conflict Matrix)
   - Detects contradictions between ANY two authors' skills (Author A vs Author B)
   - Incompatible unit systems, contradictory coordinate systems, conflicting parameter conventions
   - Polarity contradictions (always/must vs never/prohibited on the same topic)
3. Native Windows Desktop Toast Notifications to Dilu on any conflict detection.
"""

import os
import re
import sys
import json
import itertools
import subprocess

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception: pass
if hasattr(sys.stderr, 'reconfigure'):
    try: sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception: pass

# 1. Company Guardrail Invariants
CONTRADICTION_RULES = [
    {
        "id": "CAD_ZERO_DELETION",
        "description": "AutoCAD Zero Deletion & Non-Destructive Guardrail",
        "patterns": [
            r"explode.*(?:block|entity|geometry)",
            r"(?:delete|trim|remove).*(?:base geometry|landing|spine)",
            r"purge.*without.*backup"
        ],
        "safe_rule": "Base geometry, landings, and blocks must NEVER be exploded or deleted destructively."
    },
    {
        "id": "SURFACE_SNAPPING_PLAN_DRIFT",
        "description": "Surface Snapping Plan (X, Y) Coordinate Distortion",
        "patterns": [
            r"shift.*(?:x\s*,\s*y|plan\s*coord)",
            r"rotate.*(?:rafter|model\s*curve).*to\s*slope",
            r"distort.*(?:2d|plan)\s*position"
        ],
        "safe_rule": "Plan (X, Y) coordinates of lines/framing must NEVER be shifted or rotated. Only endpoint Z is adjusted."
    },
    {
        "id": "MCP_CONFIG_OVERWRITE",
        "description": "MCP Configuration Tampering",
        "patterns": [
            r"setup_all_mcp\.py",
            r"mcp_config\.json.*overwrite",
            r"replace.*RevitMcpServer"
        ],
        "safe_rule": "Skills must never overwrite the user's compiled C# MCP servers or global mcp_config.json."
    },
    {
        "id": "WPF_PITCH_BLACK",
        "description": "Executive Slate Theme Violation (Pitch Black UI)",
        "patterns": [
            r"Background\s*=\s*[\"']#000000[\"']",
            r"Background\s*=\s*[\"']#111111[\"']"
        ],
        "safe_rule": "Window backgrounds must use Executive Slate Charcoal (#2D2D30), never harsh pitch black."
    }
]

# 2. Peer-to-Peer Opposing Logic Topics (Cross-Skill Conflict Detection across ALL authors)
PEER_CONFLICT_TOPICS = [
    {
        "topic": "Coordinate System Alignment",
        "positive": [r"use\s+shared\s+coordinates", r"rely\s+on\s+shared\s+origin", r"acquire\s+coordinates", r"strictly\s+shared\s+coordinates"],
        "negative": [r"use\s+internal\s+origin", r"rely\s+on\s+project\s+base\s+point", r"ignore\s+shared\s+coordinates", r"strictly\s+project\s+base\s+point"],
        "description": "One skill prescribes Shared Coordinates while another prescribes Project Base Point / Internal Origin."
    },
    {
        "topic": "Unit System Standard",
        "positive": [r"(?:always|strictly|must)\s+use\s+(?:millimeters|metric|mm)", r"metric\s+standard\s+only", r"all\s+dimensions\s+in\s+mm"],
        "negative": [r"(?:always|strictly|must)\s+use\s+(?:feet|imperial|inches)", r"imperial\s+standard\s+only", r"all\s+dimensions\s+in\s+feet"],
        "description": "Conflicting mandatory unit systems across skills targeting the same workflow."
    },
    {
        "topic": "Revit Geometry Construction",
        "positive": [r"use\s+DirectShape(?:\.CreateElement)?", r"prefer\s+DirectShape\s+mesh", r"always\s+generate\s+DirectShape"],
        "negative": [r"(?:never|do\s+not)\s+use\s+DirectShape", r"must\s+use\s+(?:loadable|in-place)\s+FamilyInstance", r"prohibit\s+DirectShape"],
        "description": "Contradictory geometry generation guidelines (DirectShape vs FamilyInstance)."
    },
    {
        "topic": "Detail Curve vs Model Curve",
        "positive": [r"must\s+use\s+ModelCurve", r"strictly\s+create\s+3d\s+model\s+lines", r"prefer\s+model\s+curves"],
        "negative": [r"must\s+use\s+DetailCurve", r"strictly\s+create\s+2d\s+detail\s+lines", r"prefer\s+detail\s+curves"],
        "description": "Opposing curve element types prescribed for the same layout/annotation workflow."
    },
    {
        "topic": "CAD Entity Manipulation",
        "positive": [r"(?:never|do\s+not)\s+explode.*(?:block|cad)", r"preserve\s+cad\s+layers", r"zero\s+deletion"],
        "negative": [r"(?:always|must)\s+explode.*(?:block|cad)", r"purge\s+all\s+cad\s+entities", r"flatten\s+by\s+exploding"],
        "description": "One contributor mandates non-destructive CAD handling while another mandates exploding CAD entities."
    },
    {
        "topic": "Surface Snapping Plan Invariant",
        "positive": [r"(?:freeze|preserve|never\s+change|keep)\s+(?:plan|2d|x\s*,\s*y)", r"only\s+(?:adjust|change)\s+z\s+elevation"],
        "negative": [r"(?:shift|move|translate|rotate)\s+(?:plan|x\s*,\s*y|rafter\s+angle)", r"reorient\s+(?:lines|framing)\s+in\s+plan"],
        "description": "Conflicting surface snapping methods (Z-only elevation adjustment vs X/Y plan rotation/drift)."
    },
    {
        "topic": "Wall-Column Corner Joins",
        "positive": [r"flush\s+corner\s+join", r"no\s+kattak", r"join\s+geometry\s+flush"],
        "negative": [r"recessed\s+corner", r"allow\s+kattak", r"do\s+not\s+join\s+geometry"],
        "description": "Conflicting wall-column finish standards (flush corner join without kattak vs unjoined/recessed)."
    },
    {
        "topic": "Beam / Framing Z-Offset Alignment",
        "positive": [r"(?:align|offset)\s+to\s+(?:centerline|center)", r"centerline\s+z-offset"],
        "negative": [r"(?:align|offset)\s+to\s+top\s+of\s+flange", r"top\s+of\s+beam\s+flush\s+to\s+deck"],
        "description": "Conflicting framing vertical placement rules (Centerline offset vs Top of beam flush)."
    }
]

def send_windows_toast(title, body):
    """Triggers an instant, native Windows Toast notification on Dilu's screen."""
    clean_title = title.replace('"', '`"').replace("'", "’")
    clean_body = body.replace('"', '`"').replace("'", "’")
    ps_code = f"""
    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
    $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
    $textNodes = $template.GetElementsByTagName("text")
    $textNodes.Item(0).AppendChild($template.CreateTextNode("{clean_title}")) | Out-Null
    $textNodes.Item(1).AppendChild($template.CreateTextNode("{clean_body}")) | Out-Null
    $toast = [Windows.UI.Notifications.ToastNotification]::new($template)
    $notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Riyan.BIM.Sentinel")
    $notifier.Show($toast)
    """
    try:
        subprocess.Popen(["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps_code],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception:
        pass

def parse_skill_frontmatter(file_path):
    """Extract YAML frontmatter and body from SKILL.md"""
    if not os.path.exists(file_path):
        return None, ""
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        with open(file_path, 'r', encoding='latin-1', errors='replace') as f:
            content = f.read()

    frontmatter = {}
    body = content
    
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            raw_yaml = parts[1]
            body = parts[2]
            for line in raw_yaml.splitlines():
                line = line.strip()
                if line and ':' in line and not line.startswith('#'):
                    k, v = line.split(':', 1)
                    frontmatter[k.strip()] = v.strip().strip('"').strip("'")
                    
    return frontmatter, body

def audit_single_skill(skill_file_path):
    """Audits a single skill against company-wide baseline rules."""
    fm, body = parse_skill_frontmatter(skill_file_path)
    if not fm and not body:
        return {"status": "ERROR", "message": "File could not be read."}

    skill_name = fm.get("name", os.path.basename(os.path.dirname(skill_file_path)))
    author = fm.get("author", "Unknown Author")
    office = fm.get("office", "Sri Lanka & Maldives")
    discipline = fm.get("discipline", "General")
    
    clashes = []
    full_text = fm.get("description", "") + "\n" + body

    for rule in CONTRADICTION_RULES:
        for pat in rule["patterns"]:
            match = re.search(pat, full_text, re.IGNORECASE)
            if match:
                clashes.append({
                    "type": "COMPANY_RULE_CONTRADICTION",
                    "rule_id": rule["id"],
                    "description": rule["description"],
                    "matched_text": match.group(0),
                    "company_standard": rule["safe_rule"]
                })
                break

    return {
        "status": "CLASH" if clashes else "SAFE",
        "skill_name": skill_name,
        "author": author,
        "office": office,
        "discipline": discipline,
        "clashes": clashes,
        "full_text": full_text
    }

def audit_peer_conflict(skill_a_data, skill_b_data):
    """
    Audits two skills against each other to ensure NO contradiction or conflicting
    instructions exist between ANY two contributors/authors across the firm.
    """
    conflicts = []
    text_a = skill_a_data.get("full_text", "")
    text_b = skill_b_data.get("full_text", "")

    # 1. Topic Polarity Clash (A requires X, B forbids X, or vice versa)
    for topic_item in PEER_CONFLICT_TOPICS:
        pos_patterns = topic_item["positive"]
        neg_patterns = topic_item["negative"]

        a_has_pos = any(re.search(p, text_a, re.IGNORECASE) for p in pos_patterns)
        a_has_neg = any(re.search(p, text_a, re.IGNORECASE) for p in neg_patterns)
        b_has_pos = any(re.search(p, text_b, re.IGNORECASE) for p in pos_patterns)
        b_has_neg = any(re.search(p, text_b, re.IGNORECASE) for p in neg_patterns)

        if (a_has_pos and b_has_neg) or (a_has_neg and b_has_pos):
            conflicts.append({
                "type": "POLARITY_CONTRADICTION",
                "topic": topic_item["topic"],
                "description": topic_item["description"],
                "skill_a": f"{skill_a_data['skill_name']} (by {skill_a_data['author']})",
                "skill_b": f"{skill_b_data['skill_name']} (by {skill_b_data['author']})"
            })

    # 2. Strict Naming Collision with divergent logic
    if (skill_a_data["skill_name"].lower() == skill_b_data["skill_name"].lower() and
        skill_a_data["author"].lower() != skill_b_data["author"].lower()):
        conflicts.append({
            "type": "DUPLICATE_NAME_COLLISION",
            "topic": "Skill Identifier Collision",
            "description": f"Duplicate skill name '{skill_a_data['skill_name']}' created independently by different authors.",
            "skill_a": f"{skill_a_data['skill_name']} (by {skill_a_data['author']})",
            "skill_b": f"{skill_b_data['skill_name']} (by {skill_b_data['author']})"
        })

    return conflicts

def audit_incoming_skill(skill_name, content, existing_skills_dirs=None):
    """
    Audits a newly received or updated skill before writing to disk.
    Ensures that the incoming skill:
    1. Does NOT violate company guardrails.
    2. Does NOT conflict with ANY existing skill created by any team member (Peer-to-Peer).
    Returns (is_safe: bool, clash_details: dict)
    """
    fm = {}
    body = content
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            raw_yaml = parts[1]
            body = parts[2]
            for line in raw_yaml.splitlines():
                line = line.strip()
                if line and ':' in line and not line.startswith('#'):
                    k, v = line.split(':', 1)
                    fm[k.strip()] = v.strip().strip('"').strip("'")

    author = fm.get("author", "Unknown Author")
    office = fm.get("office", "Sri Lanka & Maldives")
    full_text = fm.get("description", "") + "\n" + body

    incoming_data = {
        "status": "SAFE",
        "skill_name": skill_name,
        "author": author,
        "office": office,
        "clashes": [],
        "full_text": full_text
    }

    # 1. Company Guardrail Check
    for rule in CONTRADICTION_RULES:
        for pat in rule["patterns"]:
            match = re.search(pat, full_text, re.IGNORECASE)
            if match:
                incoming_data["clashes"].append({
                    "type": "COMPANY_RULE_CONTRADICTION",
                    "rule_id": rule["id"],
                    "description": rule["description"],
                    "matched_text": match.group(0),
                    "company_standard": rule["safe_rule"]
                })
                break

    if incoming_data["clashes"]:
        send_windows_toast("Skill Sync Blocked (Company Rule)!",
                           f"Incoming skill '{skill_name}' by {author} broke rule: {incoming_data['clashes'][0]['rule_id']}")
        return False, {"type": "COMPANY_RULE_VIOLATION", "details": incoming_data["clashes"]}

    # 2. Peer-to-Peer Conflict Check against all installed skills
    if existing_skills_dirs:
        for base_dir in existing_skills_dirs:
            if not os.path.exists(base_dir):
                continue
            for item in os.listdir(base_dir):
                if item == skill_name:
                    continue  # Skip self if updating
                item_md = os.path.join(base_dir, item, "SKILL.md")
                if os.path.exists(item_md):
                    existing_skill = audit_single_skill(item_md)
                    peer_conflicts = audit_peer_conflict(incoming_data, existing_skill)
                    if peer_conflicts:
                        c = peer_conflicts[0]
                        send_windows_toast("Peer Conflict Blocked!",
                                           f"Clash between '{c['skill_a']}' and '{c['skill_b']}' on {c['topic']}!")
                        return False, {"type": "PEER_CONFLICT", "details": peer_conflicts}

    return True, {}

def audit_all_skills_in_hub(hub_dir):
    """
    Comprehensive All-vs-All Cross-Skill Conflict Matrix Audit.
    Audits every skill against company guardrails AND audits all pairs of skills
    against each other to guarantee 100% harmony across the fleet.
    """
    if not os.path.exists(hub_dir):
        return {"status": "ERROR", "message": "Hub directory does not exist."}

    skills_data = []
    company_clashes = []

    for item in sorted(os.listdir(hub_dir)):
        skill_dir = os.path.join(hub_dir, item)
        if os.path.isdir(skill_dir) and not item.startswith('.'):
            skill_md = os.path.join(skill_dir, "SKILL.md")
            if os.path.exists(skill_md):
                res = audit_single_skill(skill_md)
                skills_data.append(res)
                if res["status"] == "CLASH":
                    for c in res["clashes"]:
                        company_clashes.append({
                            "skill": res["skill_name"],
                            "author": res["author"],
                            "office": res["office"],
                            "clash": c
                        })

    peer_conflicts = []
    # Cross-audit every pair (A, B)
    for a_data, b_data in itertools.combinations(skills_data, 2):
        clashes = audit_peer_conflict(a_data, b_data)
        if clashes:
            peer_conflicts.extend(clashes)

    total_issues = len(company_clashes) + len(peer_conflicts)
    result = {
        "status": "CLASH" if total_issues > 0 else "SAFE",
        "audited_skills_count": len(skills_data),
        "company_rule_violations": company_clashes,
        "peer_to_peer_conflicts": peer_conflicts
    }

    if total_issues > 0:
        # Alert Dilu via Windows Toast!
        if peer_conflicts:
            c = peer_conflicts[0]
            send_windows_toast("Peer Skill Conflict Detected!",
                               f"Clash between '{c['skill_a']}' and '{c['skill_b']}' on {c['topic']}!")
        elif company_clashes:
            c = company_clashes[0]
            send_windows_toast("Company Rule Clash Detected!",
                               f"Skill '{c['skill']}' by {c['author']} breaks {c['clash']['rule_id']}!")

    return result

if __name__ == "__main__":
    hub = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\User\AppData\Roaming\pyRevit\Extensions\Riyan-Revit-Tools\Skills_Hub"
    print(f"[*] Auditing All-vs-All Skill Conflict Matrix in: {hub}")
    report = audit_all_skills_in_hub(hub)
    print("STATUS: " + report["status"])
    print(f"Total Audited Skills: {report['audited_skills_count']}")
    print(f"Company Violations:   {len(report['company_rule_violations'])}")
    print(f"Peer-to-Peer Clashes: {len(report['peer_to_peer_conflicts'])}")
    if report["status"] == "CLASH":
        print(json.dumps(report, indent=2))
