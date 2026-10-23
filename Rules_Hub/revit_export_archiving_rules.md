---
trigger: export_manager, batch_export, archive_previous, pdf_dwg_export, status_badges
description: Export Manager සහ Batch Export වලදී Selective Archiving, නිවැරදි Deliverable Naming, Lifecycle Execution Ordering සහ UI Status Badges පාලනය කරන නීති.
---

# Revit Export, Smart Selective Archiving සහ Lifecycle නීති

## 1. Smart Exact-Name Selective Archiving (Zero Blind Sweeping)
- **ෆෝල්ඩර් ගෙඩි පිටින් Move කිරීම දැඩිව තහනම්ය**: Output folder එකේ ඇති මුළු `PDF/` හෝ `DWG/` ෆෝල්ඩර හෝ ලිහිල් ගොනු අන්ධ ලෙස `00 PREVIOUS/` වෙත කිසි විටෙකත් move නොකළ යුතුය.
- **Strict Exact Deliverable Matching**: එම මොහොතේ export වීමට නියමිත නිශ්චිත ගොනු නාම (උදා: `Building_39.pdf`, `Building_39 - LIST OF DRAWINGS.doc`, සහ අදාළ sheets වල `.pdf` / `.dwg` නාම) සමඟ 100% exact match වන පැරණි ගොනු පමණක් move කළ යුතුය.
- **Preserve Unrelated Files**: ෆෝල්ඩරයේ ඇති වෙනත් ගොඩනැගිලි වල ගොනු (උදා: Building 40), වෙනත් drawings, text files, සහ `.rvt` ගොනු කිසි විටෙකත් ස්පර්ශ නොකළ යුතුය (100% untouched).
- **Collision-Aware Versioning**: Matching files නොමැති නම් කිසිදු archive එකක් හෝ හිස් folders නොහැදිය යුතුය. එකම දිනක එකම ගොඩනැගිල්ල නැවත export කළහොත් පමණක් version එක `02`, `03` ලෙස increment විය යුතුය.

## 2. Deliverable Naming Invariance (Zero Arbitrary Mutation)
- Combined PDF හෝ sheet deliverables සඳහා කිසිදු hardcoded prefix එකක් (උදා: `Combined_Set_`) අත්තනෝමතිකව එකතු නොකළ යුතුය.
- Naming Profile එකෙහි (`combined_schemes` / `schemes`) පරිශීලකයා සකසා ඇති scheme එක හෝ RVT Clean Base Name එක පමණක් 100% නිවැරදිව ලබාගත යුතුය.

## 3. Logical Lifecycle Ordering (Singles Before Combined)
- Final Export එකකදී ක්‍රියාත්මක වීමේ නිවැරදි පිළිවෙළ:
  1. **Single Sheets Individual Export**: එක් එක් sheet එක තනි තනිව `Pending` -> `Exporting...` -> `Done` ලෙස අවසන් විය යුතුය. ඉතිරි ඉදිරි sheets සියල්ල `Pending` තත්ත්වයේ රැඳී තිබිය යුතුය.
  2. **Combined PDF Generation**: සියලුම individual sheets `Done` වූ පසු පමණක් Combined PDF එක compile කළ යුතුය.
  3. **Drawing List Transmittal Generation**: Combined PDF සාර්ථක වූ පසු Project Drawing List එක generate විය යුතුය.

## 4. WPF UI Status Badges සහ Centered Styling Mandate
- DataGrid හි Status තීරුව කිසි විටෙකත් plain unstyled text නොවිය යුතුය. නිරන්තරයෙන්ම Centered WPF `Border` Badges පමණක් භාවිතා කළ යුතුය:
  - **Done**: `#5CB85C` (Solid Green), Text `#111111`, Centered.
  - **Exporting...**: `#FFB300` (Vibrant Amber), Text `#111111`, Centered.
  - **Error**: `#E53935` (Warning Red), Text `White`, Centered.
  - **Pending / Ready / Skipped**: Transparent background, Dim `#888888` text.
- **Reading/Loading State Protection**: File එක add වන විට හෝ කියවන විට කිසි විටෙකත් `Exporting...` නොපෙන්විය යුතුය. එය `Loading...` හෝ `Preparing...` ලෙස නිවැරදිව වෙන් කළ යුතුය.
