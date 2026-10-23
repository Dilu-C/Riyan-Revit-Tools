# Universal Process Automation, Proactive Escalation & Headless Invariants

## 1. Zero Silent Hangs & Immediate Proactive Escalation (කිසිවිටෙකත් ප්‍රශ්න සඟවාගෙන හෝ නිහඬව නොසිටීම)
- **Universal Scope**: මෙම නීතිය Revit, AutoCAD, Python, Command Line, Build හෝ වෙනත් ඕනෑම ක්‍රියාවලියකට පොදුවේ අදාළ වේ. ක්‍රියාවලිය කුමක් වුවද නීතිය එකමය.
- **Never Wait for User to Ask**: කිසිදු අවස්ථාවක කාර්යයක් අතරමග හිරවී, දෝෂයක් මතු වී හෝ අක්‍රිය වූ විට, පරිශීලකයා "මොකද වුණේ? හිරවුණාද?" කියා විමසන තෙක් නිහඬව බලා නොසිටිය යුතුය.
- **Immediate Escalation**: ස්වයංක්‍රීයව විසඳාගත නොහැකි කිසියම් බාධාවක්, දෝෂයක් (unresolvable blocker) හෝ තත්පර 120කට වඩා log/heartbeat progress එකක් නැතිවීමක් (hang) සිදුවූ වහාම, සිදුවූ දේ සහ ඇත්තම Ground-Truth තත්ත්වය ක්ෂණිකව පරිශීලකයාට හෙළිදරව් කළ යුතුය.

## 2. Revit Headless & Batch Invariants (Revit ස්වයංක්‍රීයකරණ අනිවාර්ය ආරක්ෂණ)
- **Global FailuresProcessing & DialogBoxShowing**: ඕනෑම batch Revit script එකක `Application.FailuresProcessing` සහ `Application.DialogBoxShowing` අනිවාර්යයෙන් ලියාපදිංචි කළ යුතුය. Transaction Errors/Warnings නිසා Modal Dialogs (`ADialog::doModal`) මතු වී ක්‍රියාවලිය freeze වීමට කිසිසේත් ඉඩ නොතැබිය යුතුය.
- **Inaccessible Central Model Protection**: Workshared models විවෘත කිරීමේදී Network/OneDrive වෙනස්කම් නිසා එන central model inaccessible දෝෂ වැළැක්වීමට `OpenOptions.DetachFromCentralOption = DetachAndPreserveWorksets` භාවිතා කළ යුතුය.
- **MAX_PATH (260 char) CArchiveException Guardrail**: දිගු path සහිත Central models Overwrite කිරීමේදී Windows MAX_PATH සීමාව ඉක්මවා යාම වැළැක්වීමට `C:\temp` කෙටි buffer එකක් හරහා `SaveAsCentral` සිදු කර original Central model එක නිරවුල්ව replace කළ යුතුය.
- **Per-Item Isolation**: Batch එකක තනි model එකක් අසාර්ථක වුවද, මුළු batch එකම නතර නොවී අදාළ දෝෂය log කර ඊළඟ model එකට ස්වයංක්‍රීයව යා යුතුය.

## 3. Mandatory Live Visual Console for Headless Batch Execution (අන්ධ Headless ධාවනය තහනම් කිරීම)
- **Zero Blind Headless Execution**: පරිශීලකයාට කිසිදු දෘශ්‍ය තොරතුරක් නොපෙනෙන අන්ධ "headless spinner" ක්‍රමයට දීර්ඝ කාර්යයන් ධාවනය නොකළ යුතුය.
- **Auto-Spawning Live Stream Window**: Headless batch process එකක් (Revit, AutoCAD, Python script) ආරම්භ කරන සෑම අවස්ථාවකදීම, පරිශීලකයාගේ Windows Desktop එක මත සජීවීව log එක stream වන PowerShell console window එකක් (`Start-Process powershell -ArgumentList '-NoExit', '-Command', ... Get-Content <log> -Wait`) ස්වයංක්‍රීයව විවෘත කළ යුතුය.
- **Immediate Human Visibility**: පරිශීලකයාට තමාගේම ඇස් ඉදිරිපිට කුමන ගොනුවද සැකසෙන්නේ, CPU එක ක්‍රියාත්මකද, Pass/Fail තත්ත්වය කුමක්ද යන්න තත්පරයෙන් තත්පරයට සජීවීව දැකගත හැකි විය යුතුය.

## 4. Direct Task Execution Mandate vs Tool Creation (පරිශීලක කාර්යයන් කෙලින්ම ක්‍රියාත්මක කිරීමේ නීතිය)
- **Direct Automation by Default**: පරිශීලකයා Revit models, DWG ගොනු හෝ ව්‍යාපෘති assets වල නම් වෙනස් කිරීම, upgrade කිරීම, parameter injection, linking හෝ batch processing ඉල්ලා සිටින ඕනෑම අවස්ථාවක, agent විසින් headless batch automation script එකක් මඟින් එම කාර්යය කෙලින්ම ගොනු වෙත ක්‍රියාත්මක කළ යුතුය.
- **Zero Tool Talk Without Explicit Request**: පරිශීලකයා "Tool එකක් හදන්න" හෝ "pyRevit Tool එක update කරන්න" කියා පැහැදිලිවම ප්‍රකාශ නොකරන තාක් කල්, pyRevit UI tools, ribbon buttons හෝ tool updates ගැන කිසිදු කතාවක් හෝ යෝජනාවක් නොකළ යුතුය.
- **Dual Transparency (Chat Reporting & Live Console)**:
  1. **Chat Reporting**: ක්‍රියාත්මක කිරීමට පෙර, අතරතුර සහ පසුව සිදු කරන්නේ කුමක්ද (ගොනු ලැයිස්තුව, වෙනස් වන පරාමිති, Discipline mapping, Pass/Fail ගණන්) චැට් එක තුළ ඉතා පැහැදිලිව, විනිවිදව සහ සවිස්තරව පරිශීලකයාට පෙන්විය යුතුය.
  2. **Live Visual Console**: Rule 3 අනුව පරිශීලකයාගේ desktop එක මත සජීවීව PowerShell window එකක් හරහා log එක stream කරමින්, ගොනුවෙන් ගොනුව වෙනස් වන ආකාරය ඇස් ඉදිරිපිට පෙන්විය යුතුය.


