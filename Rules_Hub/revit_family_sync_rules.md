---
trigger: titleblock_replacement, location_plan_update, batch_automation, keyplan_verification
description: TitleBlock සහ LocationPlan Families Batch Replace කිරීමේදී නිවැරදි (Checkmarked) KeyPlan එක හඳුනාගැනීම සහ Final Model එකට Enforce කිරීම පිළිබඳ නීති.
---

# Revit Family Sync & Smart KeyPlan Verification නීති

## 1. Approved Active Reference එකෙන් Live Family Extract කිරීම (Source of Truth)
- Network Drive (`\\RGLK-Drive\...`) හෝ Local Disk හි ඇති `.rfa` Files වල Date එක හෝ නම මත පමණක් පදනම්ව එය Latest/Approved Family එක යැයි උපකල්පනය නොකළ යුතුය.
- පරිශීලකයා විසින් තහවුරු කරන ලද Reference Model එක (උදා: `01-(W-SBL)`) Revit හි Open කර ඇති විට, එම Model එක තුළ පවතින Live TitleBlock සහ LocationPlan Families `doc.EditFamily(fam).SaveAs(...)` මඟින් සෘජුවම Disk එකට Extract කර Batch Automation එක සඳහා යොදාගත යුතුය.

## 2. පැරණි (Crossed-Out) KeyPlan එක මුළුමනින්ම ඉවත් කිරීම (Zero Tolerance for Outdated KeyPlan)
- වැලිපර/කලපු රේඛා 3 (3 sandbanks/lagoons) නොමැති පැරණි KeyPlan එක කිසිදු Sheet එකක හෝ View එකක නොතිබිය යුතුය.
- අවසන් වශයෙන් Save වන සෑම Revit Model එකකම Title Block සහ Location Plan තුළ තිබිය යුත්තේ පරිශීලකයා තහවුරු කළ, වැලිපර 3 සහිත නව KeyPlan එක පමණි.
- Sheet එක මත TitleBlock එක Pinned කර ඇත්නම්, පළමුව `tb.Pinned = False` කර Type ID එක අලුත් Symbol ID එකට මාරු කළ යුතුය.
- Sheet එකේ අදාළ ගොඩනැගිල්ලට අනුරූප Building Parameter එක (උදා: `39 LHK`, `34 SCK`, `40 FBO`, `38 CLN`, `35 HKB`, `36 HKW`, `37 MSQ`) Type සහ Instance Properties දෙකෙහිම `1` (ON) කර, අනෙකුත් සියලුම ගොඩනැගිලි පරාමිතීන් `0` (OFF) කළ යුතුය.
- Location Plan Sheet එකේදී TitleBlock හි `00 KEY PLAN` අගය `0` (OFF) විය යුතු අතර, Drafting View එක තුළ ඇති Detail Component එකෙහි `00 THUVARU - LOCATION PLAN` අගය `1` (ON) විය යුතුය.

## 3. Workshared Central සහ Local Model Cache පරීක්ෂාව (Local Refresh Enforcement)
- Batch Tool එක මඟින් Central Model එක සාර්ථකව Update කර Save කළද, පරිශීලකයා කලින් විවෘත කර තිබූ Local Model එක (`_dilupa.chathuranga7D32G.rvt`) කෙලින්ම විවෘත කළහොත් එහි පෙනෙන්නේ පැරණි Cached ග්‍රැෆික්ස් විය හැක.
- එබැවින් Central Model එක Update වූ පසු, පරිශීලකයාට `Create New Local` තෝරා Open කරන ලෙස හෝ `Reload Latest` / `Synchronize with Central` කරන ලෙස නිරන්තරයෙන්ම මඟපෙන්විය යුතුය.

## 4. Discipline Guardrail: Location Plan සීමා කිරීම (Architecture Only Enforcement)
- **ARC සඳහා පමණි**: LOCATION PLAN Family එක load කිරීම, Title Block හි Dedicated Location Plan Symbol යෙදීම හෝ Sheet 03 (Location Plan) සැකසීම සිදුවිය යුත්තේ `01 ARCHITECTURE` (ARC) ආකෘති සඳහා පමණි.
- **අනෙකුත් Disciplines සඳහා තහනම්**: `02 STRUCTURE`, `03 INTERIOR`, `04 FIRE`, `05 PLUMBING`, `06 SECURITY`, `07 ELECTRICAL`, `08 HVAC`, `09 LPG` යන කිසිදු ආකෘතියකට Location Plan Sheet එකක් එක් කිරීම, මාරු කිරීම හෝ Detail Component Swap කිරීම නොකළ යුතුය.
- **අනෙකුත් සියලුම Features එලෙසම පවතී**: non-ARC disciplines වලදීද TitleBlock Replacement, Batch Issued Date, Sheet Revisions Sync, Configured Parameters Injection, Building Key Plan parameter auto-tick, සහ Safe Backup (`00 PREVIOUS`) 100%ක් කිසිදු වෙනසක් නැතුව සාමාන්‍ය පරිදි ක්‍රියාත්මක විය යුතුය.

## 5. Strict Token & Boundary Matching for Family Categorization (Zero Blind Substring Matching)
- **Zero Blind Substring Matching**: NEVER use raw 3-4 letter substring checks (such as `"DOR" in filename`, `"WIN" in filename`, `"COL" in filename`) to categorize families.
- **Root Cause & Pitfalls**:
  - Raw `"DOR"` matches non-door families: `escorregador` (Portuguese playground slide), napkin `vendor`, `corridor`, `outdoor`.
  - Raw `"WIN"` matches non-window families: Double `swing` doors, `swing` gates, `twin` beds, `darwin`.
- **Mandatory Classification Rules**:
  1. **Standard Prefixes**: Always check standard company naming conventions first: `RYN_DOR_`, `RYN_WIN_`, `RYN_COL_`, `DOR_`, `WIN_`.
  2. **Whole-Word Token Boundaries**: For generic/third-party families, match against whole word boundaries (e.g. `DOOR`, `WINDOW`) separated by spaces, underscores, or hyphens, NOT arbitrary substrings inside other words.
  3. **Sanitization Guard on Catalog Load**: When indexing or loading `catalog.json`, always sanitize category assignments so that accidental false positives (e.g. playground slides or napkin vendors) are filtered to their true categories (`Arch-Other`, `Plumbing-Fixtures`).


