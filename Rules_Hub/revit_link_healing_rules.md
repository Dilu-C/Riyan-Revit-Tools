# Revit Link Integrity & Auto-Healing Rules (කැඩුණු Links ස්වයංක්‍රීයව පිළිසකර කිරීමේ නීති)

## 1. Zero Broken Links Mandate (කතිර තහනම් කිරීමේ නීතිය)
- කිසිදු Revit Model එකක් තුළ කැඩුණු හෝ Unresolved Revit Links (Project Browser හි රතු කතිර ❌) සහිතව කාර්යයන් අවසන් නොකළ යුතුය.
- Model එකක් Rename වූ විට හෝ Path වෙනස් වූ විට, එම ගොඩනැගිල්ලට සම්බන්ධ සියලුම Models (ARC, STR, MEP, FIRE, PLUMB) හි Links පරීක්ෂා කර බිඳී ඇති Links හඳුනාගත යුතුය.

## 2. Automated Smart Re-pathing (ස්වයංක්‍රීය නැවත සම්බන්ධ කිරීම)
- පැරණි නාමය සහ නව කෙටි නාමය (Discipline tag: ARC, STR, FIRE, PLUMB, ELEC, HVAC) ගලපා `TransmissionData` හෝ `RevitLinkType.LoadFrom` හරහා නව ගොනු මාවතට (New Target Path) ස්වයංක්‍රීයව Re-path කළ යුතුය.
- Model එක විවෘත කළ විට සියලුම Links සාර්ථකව Load වී රතු කතිර ඉවත්ව පවතින බව 100% තහවුරු කළ යුතුය.

## 3. Windows MAX_PATH (260 Char) Silent Failure Guardrail
- Revit API හෝ pyRevit හරහා කිසියම් RVT ලින්ක් එකක් Load කිරීමට හෝ Open කිරීමට පෙර, සැමවිටම Target Path එකේ අකුරු ගණන (`len(path)`) පරීක්ෂා කළ යුතුය.
- Path එක අකුරු 250 ට වඩා දිගු නම්, Revit විසින් "File doesn't exist" යනුවෙන් සාවද්‍ය දෝෂයක් ලබා දෙන බැවින්, කිසිවිටෙක ගොනුව නැතැයි අනුමාන නොකළ යුතුය.
- එවැනි විටෙක වහාම කෙටි මාවතක් (Shorter Mirror Path හෝ 8.3 Short Path හෝ Symlink) භාවිත කර Link එක Load කළ යුතුය.
