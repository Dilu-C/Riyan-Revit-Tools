---
trigger: always_on
description: Guardrail prohibiting automated git push commands in the background to prevent hung tasks and credential deadlocks.
---

# Git & Remote Push Execution Guardrails

## 1. Never Run Automated `git push` via Terminal
- Under no circumstances should the agent execute `git push` via terminal commands or background tasks.
- Terminal-based `git push` on Windows frequently triggers blocking GUI/browser authentication prompts or hangs indefinitely as a background task.

## 2. Respect User's GitHub Desktop Workflow
- Prepare all local files, repositories, commits, and structures locally as requested.
- Once local changes are committed or staged, inform the user that their changes are ready for them to push with 1 click via **GitHub Desktop** (`Push origin`).
- Never attempt to force, automate, or background-push to remote repositories.

## 3. Mandatory Dual-Location Sync & Multi-Repo Management for GitHub Desktop
- **Repository 1: Riyan-Revit-Tools**
  - **Revit Runtime Location**: `C:\Users\User\AppData\Roaming\pyRevit\Extensions\Riyan-Revit-Tools`
  - **GitHub Desktop Tracked Location**: `C:\Users\User\Desktop\Riyan-Revit-Tools`
  - **Mandatory Mirroring Before Commit**: Whenever updates are prepared for GitHub, mirror updated files from AppData to Desktop (excluding `.git`), stage and commit directly in `C:\Users\User\Desktop\Riyan-Revit-Tools`.
- **Repository 2: Dilu-BIM-Automation**
  - **GitHub Desktop Tracked Location**: `C:\Users\User\Documents\GitHub\Dilu-BIM-Automation`
  - **Revit Runtime Location**: Directly registered in `%APPDATA%\pyRevit\pyRevit_config.ini` `userextensions` as `C:\Users\User\Documents\GitHub\Dilu-BIM-Automation` (Direct physical discovery, zero symlinks).
  - Stage and commit directly in `C:\Users\User\Documents\GitHub\Dilu-BIM-Automation`.
- **Universal Revit 2027+ Guardrail**: All code, features, and fixes across BOTH repositories must strictly maintain 100% compatibility with Revit 2021 through Revit 2027+ (.NET 8, CPython 3, 64-bit ElementId, ForgeTypeId).

## 4. Zero Legacy & Markdown Artifacts in Extension Runtime (Zero Stray File Guardrail)
- **Zero Markdown in Runtime**: `*.extension` runtime directories (`Riyan.extension`, `Dilu.extension`) MUST NEVER contain `*.md` files (such as `README.md`, `GEMINI.md`), `*.txt` documents (except mandatory `version.txt`), `.idea`, `extension.json.txt`, `.gitattributes`, `.gitignore`, or unused legacy folders (`Other`, backups). Documentation belongs strictly at the repository root.
- **Universal Multi-Pathway Purge Parity**: Every update and sync mechanism across the ecosystem—including:
  1. Offline/Standalone Updater (`Update_Riyan_Tools.bat`)
  2. In-Revit Ribbon Updater (`CheckForUpdates.pushbutton\script.py`)
  3. Startup Self-Healing Engine (`startup.py`)
  4. Local AppData Mirroring Scripts
  MUST enforce identical, comprehensive deletion of `*.md`, `.idea`, `extension.json.txt`, `Other`, and non-existent network paths (`\\RGLK-Drive\...`).
- **Single-Click User Resolution**: Never leave manual cleanup to the user. Running the update via BAT or clicking Update inside Revit must unconditionally wipe all legacy remnants automatically.
- **Mandatory Version Bump on Release**: Whenever any fixes, features, or purges are committed to be delivered to clients, ALWAYS bump the version in `version.txt` and `Riyan.extension\version.txt` so the In-Revit updater detects the update and does not falsely claim "System Up to Date".

### 4.1 Mandatory Deterministic Ribbon Layout (Zero Floating/Shuffled Buttons)
- **Mandatory Panel-Level bundle.yaml**: Every single panel folder (e.g. `Export.panel`, `Structure.panel`, `Tags.panel`, `Riyan Library.panel`, etc.) MUST contain a `bundle.yaml` explicitly declaring its internal button order (`layout: [...]`). Never allow pyRevit to discover buttons via arbitrary filesystem sorting.
- **Mandatory Tab-Level Layout Order**: `Riyan.tab\bundle.yaml` must explicitly declare all panels in exact sequence:
  `[System, Coordination, Structure, Modeling, Tags, Export, MOT, Door Window Schedules, Riyan Library]`
- **Zero OS-Dependent Ordering**: All client machines across the entire company must render the exact identical ribbon button sequence bit-for-bit.

### 4.2 Clean-Slate Extension Replacement (Zero Merge-Copy Guardrail)
- **Never Merge-Copy over Target Extension**: When updating via BAT or In-Revit updater, NEVER run blind `Copy-Item` on top of an existing extension folder.
- **Mandatory Atomic Clean-Slate Installation**:
  1. Wipe pyRevit UI Cache (`%APPDATA%\pyRevit\Cache\*`, `%APPDATA%\pyRevit\20*`) completely.
  2. Perform an atomic clean-slate wipe of the target extension directory before copying the fresh version (or clean mirror sync via `robocopy /MIR` or PowerShell purge of untracked items).
  3. Ensure obsolete panel folders (e.g. `Tool.panel`, `About.panel`) and legacy files are unconditionally wiped from disk on every startup (`startup.py`) and updater execution.

## 5. Strict Default Branch Mandate (`main` Branch Only)
- **Always Work on `main` Branch**: All regular development, bug fixes, releases, updates, and sync operations MUST strictly be committed directly to the `main` branch.
- **Zero Work on `dev` Unless Explicitly Requested**: Under no circumstances should the agent create, switch to, or commit changes to the `dev` branch unless the user explicitly commands: *"dev එකේ කරන්න"* (do it in dev).
- **Ensure Active Branch is `main`**: Always ensure the checked-out branch in local working repositories is `main` so the user's GitHub Desktop remains clean, predictable, and focused on `main`.

## 6. Strict Version Lock & In-Revit Multi-PC Rollout Awareness (Zero Rogue Version Escalation)
- **Zero Unprompted Version Escalation**: NEVER bump major or minor version numbers (e.g. jumping from `2.5.x` to `2.6.x` or `2.7.x`) without explicit, direct instructions from the user.
- **Client Deployment Reality (Multi-PC Awareness)**:
  - Tools are deployed across 100+ company PCs. Users cannot and will not manually run BAT scripts across 100 PCs.
  - Client PCs rely entirely on the In-Revit ribbon updater (`CheckForUpdates.pushbutton`), which compares the local installed `version.txt` against `https://raw.githubusercontent.com/.../version.txt`.
  - The In-Revit updater prompts the user ONLY when the online version is strictly newer than the local version (`is_newer_version(online, local)`).
  - Version bumps must be treated as formal deployment events, locked tightly to the active authorized release series (e.g. strictly adhering to `2.5.10` per user mandate), ensuring zero friction or broken update alerts across client machines.

## 7. Strict Prohibition of Version Checking & Startup Popups in Dilu (Zero Nag Screen Guardrail)
- **Personal Extension Mandate**: `Dilu.extension` is strictly for personal use by the developer. It has zero version tracking requirements and requires zero client distribution.
- **Zero Cross-Repo Version Leaks**: `Dilu.extension` MUST NEVER fetch, check, or compare version information from `Riyan-Revit-Tools` or any other external repository. Both repositories are strictly independent.
- **Zero Startup Popups / Toasts / Threads**: Under NO circumstances may `Dilu.extension` launch background threads, timers, or processes that display popup dialogs, WPF toasts, balloon tooltips, or nag screens upon Revit startup.
- **Zero Update Logic in Code**: `Dilu.extension` codebase must NEVER contain `get_versions()`, `is_newer_version()`, `show_update_toast()`, `check_for_updates()`, or GitHub version fetching URLs.
- **Strictly Silent Startup**: Startup scripts in `Dilu.extension` (`startup.py`) must execute silently and safely without interrupting the user.

## 8. Strict Change Preservation & Zero-Regression Guardrail (මෑත වෙනස්කම් Revert නොකිරීමේ නීතිය)
- **Zero Reversion of Recent Work**: කිසිදු අවස්ථාවක පරිශීලකයා විසින් හෝ මෑත සංවර්ධන සැසිවාරයන්හිදී කරන ලද කේත, UI සැකසුම්, button configurations, හෝ script updates නැවත පැරණි තත්ත්වයට (revert) පත් කිරීම, අත්හැර දැමීම හෝ overwrite කිරීම 100% තහනම් වේ.
- **Pre-Edit History & Diff Audit**: යම් ගොනුවක් සංස්කරණය කිරීමට හෝ commit කිරීමට පෙර, `git log -n 5` සහ လက်ရှိ working tree එක පරීක්ෂා කර, මෑතකදී කරන ලද යාවත්කාලීනයන් කිසිවක් අහම්බෙන් මැකී හෝ undo වී නොමැති බව තහවුරු කළ යුතුය.
- **Preserve Intentional Layouts**: `Dilu.tab\bundle.yaml` ඇතුළු ribbon layouts වල පරිශීලකයා තබා ඇති අනුපිළිවෙල (විශේෂයෙන් `Coordination` ඇතුළු ප්‍රධාන panels) කිසිවිටෙකත් ඉවත් නොකළ යුතුය.

## 9. Absolute Dual-Repo Isolation (Dilu සහ Riyan අතර නිරපේක්ෂ ස්වාධීනත්වය)
- **Zero Cross-Repo Contamination**: `Dilu-BIM-Automation` සහ `Riyan-Revit-Tools` යනු එකිනෙකට සම්පූර්ණයෙන්ම වෙනස්, ස්වාධීන repositories දෙකකි.
- **Never Mirror/Copy Across Repos**: එක් repository එකක ඇති panel folders, scripts, shared parameters, හෝ assets කිසිවිටෙකත් පරිශීලකයාගේ සෘජු විධානයකින් තොරව අනෙක් repository එක තුළට copy කිරීම, merge කිරීම හෝ paste කිරීම දැඩි ලෙස තහනම් වේ.
- **Zero Unprompted Panel Injections**: `Dilu.tab` වෙත `Riyan` හි panels බලහත්කාරයෙන් පැටවීම හෝ `Dilu` හි layout එක Riyan මට්ටමට මාරු කිරීම නොකළ යුතුය.


