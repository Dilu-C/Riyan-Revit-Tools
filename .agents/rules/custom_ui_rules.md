---
trigger: ui_design, pyrevit_dialogs, forms_alert, popup_window
description: pyRevit පෙරනිමි (Default) forms.alert හෝ TaskDialog භාවිතය තහනම් කිරීම සහ සියලුම UI Dialogs අභිරුචි (Custom Dark Theme WPF) ශෛලියෙන් පමණක් සැකසීමේ නීතිය.
---

# Revit UI Dialogs සහ Alert Windows අභිරුචිකරණ නීති (Custom UI Mandate)

## 1. pyRevit Default `forms.alert()` හෝ `forms.toast()` භාවිතය දැඩිව තහනම්ය (Never Use Default Alerts)
- pyRevit හි පෙරනිමි සුදු පැහැති `forms.alert()` හෝ Windows Default Message Box කිසි විටෙකත් භාවිතා නොකළ යුතුය.
- එම පෙරනිමි popups අපගේ Riyan / Dilu BIM Automation පද්ධතියේ Modern Dark UI Theme එකට නොගැළපෙන අතර පරිශීලක අත්දැකීමට බාධාවකි.

## 2. සෑම Alert සහ Completion Modal එකක්ම Custom Dark Theme WPF මඟින් සැකසිය යුතුය
- ඕනෑම alert එකක්, success message එකක් හෝ warning එකක් සඳහා අපගේ Custom WPF Window (`CustomAlertWindow`) භාවිතා කළ යුතුය:
  - **Background:** `#111111` (Master Dark)
  - **Title Bar:** `#1A1A1A` with Accent icon (`#802F2D`) සහ DragMove සහය
  - **Border:** `#3A3A3A` BorderThickness=1
  - **Text Color:** `#CCCCCC` with LineHeight=18
  - **Button:** `#802F2D` (Normal) -> `#9E3A38` (Hover), CornerRadius=3, Foreground White.
  - **Icons:** Unicode Characters (Success: `✔`, Warning: `⚠`, Error: `✖`).

## 3. Batch Tools වලදී Headless Execution (Zero Modal Interruptions)
- Batch Processing මෙවලම් (උදා: `Batch_TitleBlock_Replacer`) ක්‍රියාත්මක වන විට, එක් එක් Model එක සඳහා popups/alerts නොපෙන්විය යුතුය.
- සියලුම විස්තර Progress Log එකට ලියවිය යුතු අතර, සම්පූර්ණ Batch එක අවසානයේ පමණක් අපගේ Custom Manager Summary Dialog එක පෙන්විය යුතුය.
