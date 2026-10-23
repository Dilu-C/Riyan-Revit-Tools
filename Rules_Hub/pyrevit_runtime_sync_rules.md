---
trigger: riyan_tools, pyrevit, export_manager, batch_export, git_commit, release_update, update_issue, updater_script, clean_slate_update
description: pyRevit Runtime (AppData) සහ Desktop සංවර්ධන පරිසරය අතර කේත desync වීම, Update පටලැවිලි, පැරණි ගොනු ඉතිරිවීම (Ghost files) වැළැක්වීම සහ Clean-Slate Update නීති.
---

# pyRevit Runtime Environment & Zero-Desync Sync Rules

## 1. තනි මූලාශ්‍රය පමණක් සංස්කරණය කිරීම (Single Canonical Source)
- සියලුම කේත සංස්කරණයන්, bug fixes, නව features සහ git commits සිදු කළ යුත්තේ **`C:\Users\User\Desktop\Riyan-Revit-Tools`** හි පමණි.
- AppData ෆෝල්ඩරය තුළ කිසිවිටෙකත් වෙනම code development සිදු නොකළ යුතුය.

## 2. ක්ෂණික සහ අනිවාර්ය Active Runtime Mirroring (Immediate AppData Sync)
- Desktop ෆෝල්ඩරයේ කිසියම් `.py`, `.xaml`, `.json` හෝ asset එකක් වෙනස් කළ සැණින්, එම සියලුම වෙනස්කම් ක්ෂණිකව `%APPDATA%\pyRevit\Extensions\Riyan-Revit-Tools` වෙත force-copy කර සමමුහුර්ත කළ යුතුය.
- කිසිදු අවස්ථාවක AppData ෆෝල්ඩරය යාවත්කාලීන නොකර පරිශීලකයාට "Revit එකෙන් බලන්න" හෝ "Reload කරන්න" යැයි නොපැවසිය යුතුය.

## 3. AppData Git Drift & Branch Lock (Zero Divergence Guardrail)
- `%APPDATA%\pyRevit\Extensions\Riyan-Revit-Tools` හි `.git` repository එකක් පවතී නම්, එය කිසිවිටෙකත් වෙනත් branches හෝ test commits වලට මාරු නොවිය යුතුය.
- එය නිරන්තරයෙන්ම ප්‍රධාන `origin/main` ශාඛාවට 100% hard reset වී තිබිය යුතුය.

## 4. pyRevit දෝෂ ක්ෂණික විමර්ශන ප්‍රොටෝකෝලය (Zero-Confusion Diagnostic Protocol)
- පරිශීලකයා "ටූල් එකේ වෙනස්කම් පේන්නේ නෑ", "පරණ එකක් පේන්නේ", හෝ "Update වෙන්නේ නෑ" යැයි පැවසූ සැණින්, කිසිදු අනුමානයක් නොකර පහත පියවර 4 අනුපිළිවෙලින් ක්‍රියාත්මක කළ යුතුය:
  1. **පළමු පියවර**: `%APPDATA%\pyRevit\pyRevit_config.ini` කියවා Revit එක active load කරගන්නා exact path එක තහවුරු කරගැනීම.
  2. **දෙවන පියවර**: එම active runtime path එකේ ඇති `script.py` සහ `UI.xaml` වල file size සහ timestamp Desktop canonical repo එක සමඟ සංසන්දනය කිරීම.
  3. **තෙවන පියවර**: AppData ෆෝල්ඩරයේ `git status` පරීක්ෂා කර branch drift එකක් වී ඇත්දැයි තහවුරු කිරීම.
  4. **හතරවන පියවර**: වෙනසක් ඇත්නම්, වහාම Desktop එකෙන් AppData වෙත force sync කර `git reset --hard origin/main` ධාවනය කිරීම.

## 5. පරිසර සමානතා විගණනය (Mandatory Environment Parity Audit)
- ඕනෑම release එකකට පෙර හෝ පරිශීලකයාට පරීක්ෂා කිරීමට ලබා දීමට පෙර පහත විගණනය අනිවාර්යයෙන්ම ධාවනය කළ යුතුය:
  1. Desktop සහ AppData හි ප්‍රධාන ගොනු ප්‍රමාණයන් (file size & hash) සංසන්දනය කිරීම.
  2. `Export Manager.pushbutton\script.py` සහ `ExportUI.xaml` හි Preview sidebar සහ නව කේත අඩංගු බව තහවුරු කිරීම.
  3. `Batch Export.pushbutton\script.py` සහ `UI.xaml` හි නව WrapPanel, Window Pinning සහ Context Menu අඩංගු බව තහවුරු කිරීම.

## 6. Update Blind Spot වැළැක්වීම සහ File Integrity Guardrail
- Updater එක ක්‍රියාත්මක කිරීමේදී `version.txt` එක පමණක් විශ්වාසය නොතබා, core tools වල file sizes / hashes සංසන්දනය කර අසමාන නම් ස්වයංක්‍රීයව Force Repair / Re-download සිදු කළ යුතුය.
- පරිශීලකයාට ඕනෑම මොහොතක 1-click එකෙන් active AppData folder එක Desktop එකට හෝ GitHub main එකට mirror කරගැනීමට `Repair / Force Sync` පහසුකම ලබා දිය යුතුය.

## 7. pyRevit Multi-Year Cache & Compilation Cleanup (Revit 2021-2027+)
- නව අනුවාදයක් deploy කිරීමේදී හෝ දෝෂයක් නිරාකරණය කිරීමේදී, `%APPDATA%\pyRevit\20*\` (2021, 2022, 2023, 2024, 2025, 2026, 2027+) හි ඇති සියලුම පැරණි compiled `.dll` සහ `__pycache__` ඉවත් කර, Revit එකට අලුත්ම කේතය recompile කර ගැනීමට මඟ පෑදිය යුතුය. කිසිවිටෙකත් තනි වසරක් (උදා: `2026` පමණක්) hardcode නොකළ යුතුය.

## 8. Clean-Slate / Zero-Ghost Update නීතිය (පැරණි ගොනු 100% Wipe කර අලුත් එක පමණක් රඳවා ගැනීම)
- **Zero Ghost Tolerance**: GitHub එක හරහා හෝ වෙනත් ක්‍රමයකින් update එකක් නිකුත් කරන සෑම අවස්ථාවකදීම, client PC වල පැරණි tools, rename කරන ලද buttons, අත්හැර දැමූ scripts හෝ පැරණි cache කිසිවක් ඉතිරි වීමට කිසිසේත්ම ඉඩ නොතැබිය යුතුය.
- **Wipe Before Deploy**: ඕනෑම Update Batch script එකක් (`Update_Riyan_Tools.bat`), installer එකක් හෝ deployment script එකක් මඟින් අලුත් ගොනු copy කිරීමට පෙර, පහත සඳහන් සියල්ල අනිවාර්යයෙන්ම Clean Wipe / Delete කළ යුතුය:
  1. `%APPDATA%\pyRevit\Extensions\Riyan.extension` සම්පූර්ණයෙන්ම rmdir / Remove-Item කිරීම.
  2. `%APPDATA%\pyRevit\Extensions\Riyan-Revit-Tools` තුළ ඇති සියලුම පැරණි උප-ෆෝල්ඩර සහ ගොනු 100% purge කර ඉවත් කිරීම (ක්‍රියාත්මක වන bat එක lock වී ඇත්නම් හැර අන් සියල්ල purge කිරීම).
  3. `%APPDATA%\pyRevit\20*\`, `__pycache__` සහ compiled cache සම්පූර්ණයෙන්ම erase කිරීම (2021 සිට 2027+ දක්වා සියලුම Revit versions).
- **Fresh Overwrite**: ඉන් අනතුරුව පමණක් GitHub හි main ශාඛාවෙන් බාගත කළ අලුත්ම fresh package එක අදාළ ෆෝල්ඩර වෙත තැන්පත් කළ යුතුය.
- **Verifiable Clean State**: Update එක අවසන් වූ පසු client පරිසරයේ තිබිය යුත්තේ GitHub main එකේ පවතින අලුත්ම ගොනු සංචිතය පමණක් බව තහවුරු කළ යුතුය.

## 9. Ribbon Item නම් වල අනන්‍යතාවය සහ Duplicate ගැටුම් වැළැක්වීම (Zero Ribbon Duplicate Guardrail)
- **Unique Item Naming**: කිසිදු Ribbon Panel එකක් හෝ Tab එකක් තුළ එකම නම ඇති PushButton, PullDown හෝ SplitButton දෙකක් නොතිබිය යුතුය (උදා: `Update.pushbutton` එකක් තිබියදී `Update.pulldown` දැමීමෙන් Revit Ribbon API එක `The name already exists` ලෙස බිඳවැටේ).
- **Button Type වෙනස් කිරීමේදී Cache Purge අනිවාර්යය**: PushButton එකක් Pulldown එකක් බවට පත් කළ විට, client PC වල pyRevit Cache එක 100% මකා දැමිය යුතුය.

## 10. සියලුම Icons 96x96px ප්‍රමාණයට සීමා කිරීම (Strict Icon Dimension Guardrail)
- **Strict Max 96x96**: pyRevit ribbon එක වේගවත්ව load වීම සඳහා සහ warnings වැළැක්වීමට, extension එකේ ඇති සියලුම `icon.png` ගොනු උපරිම 96x96 pixels ප්‍රමාණයට resize කර තිබිය යුතුය. කිසිවිටෙකත් 1024x1024 uncompressed icons repo එකට ඇතුළත් නොකළ යුතුය.

## 11. බහු-ස්ථාන පැරණි Extension Clean Wipe (Multi-Location Purge Protocol)
- Updater Script එක මඟින් අලුත් කේතය දැමීමට පෙර, පහත සියලුම ස්ථානවල ඇති ඕනෑම Riyan extension පිටපතක් ක්ෂණිකව Wipe/Delete කළ යුතුය:
  1. `%APPDATA%\pyRevit\Extensions\Riyan.extension`
  2. `%APPDATA%\pyRevit\Extensions\Riyan-Revit-Tools-main`
  3. `%PROGRAMDATA%\pyRevit\Extensions\Riyan*`
  4. `C:\Program Files\pyRevit-Master\extensions\Riyan*`
- Client PC එකක තිබිය යුත්තේ `%APPDATA%\pyRevit\Extensions\Riyan-Revit-Tools\Riyan.extension` යන තනි, නිවැරදි මූලාශ්‍රය පමණි.

## 12. පූර්ව-Commit අනිවාර්ය XAML සහ Python Syntax පරීක්ෂාව (Pre-Commit Zero-Crash Check)
- ඕනෑම UI වෙනසක් (`.xaml` හෝ Python strings) commit කිරීමට පෙර:
  1. `[System.Windows.Markup.XamlReader]::Parse()` මඟින් parse කර බැලීම අනිවාර්ය වේ (`LetterSpacing` වැනි නොගැලපෙන attributes කිසිවිටෙකත් ඇතුළත් නොකිරීම).
  2. සියලුම pushbutton folders තුළ වලංගු `script.py` ගොනුවක් පවතින බව ස්වයංක්‍රීයව තහවුරු කිරීම (හිස් folders තිබීම තහනම්).

## 13. ස්වයංක්‍රීය පසුබිම් ස්වයං-සුවපත් කිරීමේ ප්‍රොටෝකෝලය (Zero-Touch Self-Healing Protocol)
- **Silent Background Healing on Startup**: Revit එක ආරම්භ වන සෑම අවස්ථාවකදීම `startup.py` මඟින් පසුබිමෙන් (background daemon) පහත පිරිසිදු කිරීම් ස්වයංක්‍රීයව සිදු විය යුතුය:
  1. `%APPDATA%\pyRevit\Extensions\Riyan.extension` නමින් root එකේ පවතින පැරණි duplicate ෆෝල්ඩරය auto delete කිරීම.
  2. `%APPDATA%\pyRevit\Extensions\Riyan-Revit-Tools-main` පවතී නම් auto delete කිරීම.
  3. `Riyan.tab\About.panel` හෝ script රහිත හිස් බොත්තම් පවතී නම් auto purge කිරීම.
  4. `pyRevit_config.ini` හි `userextensions` පිරිසිදු කර `Riyan-Revit-Tools` පමණක් තනි මූලාශ්‍රය ලෙස තහවුරු කිරීම.
- කිසිදු පරිශීලකයෙකුට හෝ මාලදිවයිනේ කණ්ඩායමට අතින් folders rename කිරීමට හෝ delete කිරීමට ඉඩ නොතබා, Revit open කරද්දීම background එකෙන් system එක self-heal විය යුතුය.

## 14. ගෝලීය යාවත්කාලීන සමමුහුර්තකරණය (Global Single-Source-of-Truth Sync)
- **Single Deployment Pipeline**: Updater bat file එකක් භාවිත කළද, නැතහොත් Revit ඇතුළත `System > Update` බොත්තම භාවිත කළද, ක්‍රියාත්මක වන්නේ GitHub main ශාඛාවේ ඇති එකම පිරිසිදු package එක පමණි.
- **Backward Compatible Updaters**: මීට පෙර Maldives හෝ වෙනත් පරිගණක වලට යවන ලද පැරණි bat file එකක් run කළද, එය බාගත කරන්නේ අපගේ අලුත්ම GitHub main package එක බැවින්, අලුත් package එකේ ඇති self-healing කේතය මඟින් එම පැරණි පරිගණකයද ක්ෂණිකව නවතම තත්ත්වයට ස්වයංක්‍රීයව පත් කෙරේ.

## 15. පූර්ව-Commit නිරපේක්ෂ පරීක්ෂණ අනිවාර්යය (Pre-Push Zero-Tolerance Gatekeeper)
- GitHub Desktop එකෙන් push කිරීමට පෙර පහත කරුණු 4 සම්පූර්ණ වී තිබීම අනිවාර්ය වේ:
  1. **XAML Parsing Test**: සියලුම `.xaml` ගොනු සහ Python strings තුළ ඇති XAML `XamlReader::Parse()` මඟින් 0 errors ලෙස pass වීම.
  2. **Icon Dimension Test**: සියලුම `icon.png` උපරිම 96x96px බවට තහවුරු කිරීම.
  3. **Batch Parser Test**: Updater bat file එක cmd.exe මඟින් කිසිදු syntax error එකකින් තොරව execute වන බව තහවුරු කිරීම.
  4. **Clean Tree Audit**: අනවශ්‍ය stray files (echo, zips, temp files) 0ක් බවට තහවුරු කිරීම.

## 16. Dynamic Ribbon Button Addition & Runtime .NET Assembly Class Lock (Zero "Wrong Full Class Name" Guardrail)

### 16.1. සජීවී සැසිය තුළ Fallback Trigger කිසිවිටෙකත් ඉවත් නොකිරීම (Zero In-Session Trigger Deletion Guardrail)
- **Strict Prohibition on Fallback Deletion**: Revit ක්‍රියාත්මක වන අතරතුර (active session) අලුතින් Ribbon PushButton එකක් හැදුවද, පවතින Host Tool එක (උදා: `Site Generator`) තුළ ඇති in-session trigger බොත්තම (`📦 Batch Link Stager...`) කිසිදු හේතුවක් මත delete කිරීම, සැඟවීම හෝ unhook කිරීම **100% තහනම් වේ**.
- **Dual Availability During Transition**: පරිශීලකයා Revit restart කර අලුත් Ribbon button එක සාර්ථකව ක්‍රියාත්මක වන බව තහවුරු කරන තුරු, Host tool එක තුළ ඇති බොත්තම අනිවාර්යයෙන්ම පවත්වාගත යුතුය.

### 16.2. අලුත් Ribbon බොත්තම Click කිරීමට නොපැවසීම (Zero Premature Ribbon Delegation)
- **Zero Premature Ribbon Direction**: Revit restart කර නොමැති සජීවී session එකකදී, පරිශීලකයාට "Ribbon එකේ තියෙන අලුත් button එක click කරන්න" යැයි කිසිවිටෙකත් නොපැවසිය යුතුය.
- **Mandatory Safe Direction**: සැමවිටම පරිශීලකයාට පැහැදිලිව මඟ පෙන්විය යුත්තේ:
  > *"Revit restart වන තුරු අලුත් Ribbon button එකෙන් 'Wrong Full Class Name' දෝෂය පැමිණිය හැක. එබැවින් මෙම session එක තුළදී Site Generator එක ඇතුළේ ඇති බොත්තම මඟින් කිසිදු දෝෂයකින් තොරව tool එක විවෘත කරගන්න."*

### 16.3. pyRevit Cache Invalidation & Next-Startup Guarantee
- අලුත් pushbutton එකක් repo එකට commit කිරීමට පෙර, `%APPDATA%\pyRevit\20*\` හි ඇති පැරණි `*Dilu*.dll` සහ `*Dilu*.json` cache wipe කර ඊළඟ startup එකේදී clean DLL compilation එකක් සහතික කළ යුතුය.
- එවිට ඊළඟ වතාවේ Revit open වන විට pyRevit විසින් අලුත් button එකේ class එකද ඇතුළත් කර fresh DLL එකක් කිසිදු error එකක් නොමැතිව compile කරගනී.



