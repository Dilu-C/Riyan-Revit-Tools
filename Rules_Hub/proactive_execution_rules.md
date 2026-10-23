# Proactive Progress Reporting & Task Visibility Rules

## 1. High-Frequency Proactive Updates (තත්පර 15-30 සජීවී කාල පරාසය)
- පසුබිමෙන් ධාවනය වන දීර්ඝ කාර්යයන් (Revit batch updates, model processing, file operations, CAD tasks) ක්‍රියාත්මක වන විට, උපරිම වශයෙන් සෑම තත්පර 15-30 කට වරක්ම පරිශීලකයාට සජීවී ප්‍රගති වාර්තාවක් (Live Progress Update) ලබා දිය යුතුය.
- පරිශීලකයා විමසන තෙක් කිසිසේත්ම බලා නොසිටිය යුතුය. Agent විසින් `schedule` (Timer) හෝ සජීවී ලොග් කියවීම් හරහා නිරන්තර ප්‍රගතිය ඉදිරිපත් කළ යුතුය.

## 2. Live Task Transparency & Exact Metrics
- සෑම update එකකදීම:
  1. මේ වන විට අවසන් වූ Models/Files ගණන සහ ප්‍රතිශතය.
  2. මේ මොහොතේ සැකසෙමින් පවතින Model එක සහ Discipline එක.
  3. සාර්ථක/අසාර්ථක තත්ත්වය සහ Update වූ fields ප්‍රමාණය.
  පැහැදිලිව, සරල කතාබස් සිංහලෙන් ඉදිරිපත් කළ යුතුය.
