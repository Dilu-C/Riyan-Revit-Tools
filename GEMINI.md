# Revit API & pyRevit Best Practices

When working on scripts in this repository, strictly adhere to the following rules based on past troubleshooting:

1. **Legend Component Copying**: CopyElements between different Legend Views fails silently if a translation transform is passed in the same method call.
   - **Correct Approach**: Duplicate the base view (pristine_view.Duplicate()), copy elements *within* the same duplicated view using DB.Transform.Identity, and then use MoveElements to position them. Finally, delete the original template elements.

2. **ScheduleSheetInstances on Titleblocks**: Titleblocks often contain Revision Schedules, which Revit treats as ScheduleSheetInstances on the sheet. Revision Schedules **do not support filters**.
   - **Correct Approach**: When iterating ScheduleSheetInstances on a sheet to find a specific schedule, always verify the category of the schedule definition (sched.Definition.CategoryId.IntegerValue == cat_enum.IntegerValue) to filter out Revision Schedules.

3. **Schedule Bounding Boxes**: The bounding box of a newly placed ScheduleSheetInstance may not accurately reflect its filtered height immediately. 
   - **Correct Approach**: Always place the schedule, commit it in a SubTransaction, and call doc.Regenerate() before attempting to use its BoundingBox for dynamic placement of other elements.

4. **Python Scoping Trap (UnboundLocalError)**: 
   - **Correct Approach**: Avoid importing modules locally (e.g., rom pyrevit import forms) inside except blocks if that variable is intended to be used or imported elsewhere in the same function scope. Rely on global imports at the top of the file.

5. **List Instantiation for ElementIds**: When passing lists of ElementId to Revit API methods like doc.Delete() or MoveElements(), always construct them explicitly using System.Collections.Generic.List[DB.ElementId]().

6. **Active Document Caching (pyRevit Cached Engines)**:
   - pyRevit à·€à¶½ Cached Engines à¶šà·Šâ€à¶»à·’à¶ºà·à¶­à·Šà¶¸à¶š à·€à¶± à·€à·’à¶§, module-level variables (à¶‹à¶¯à·: `doc = revit.doc` à·„à· `uidoc = revit.uidoc`) à¶´à¶»à¶« document à¶‘à¶šà¶§à¶¸ à¶½à·œà¶šà·Š à·€à·“ à¶´à·à·€à¶­à·’à¶º à·„à·à¶š.
   - **à¶±à·’à·€à·à¶»à¶¯à·’ à¶šà·Šâ€à¶»à¶¸à¶º**: à·ƒà·à¶¸à·€à·’à¶§à¶¸ main execution à¶‘à¶š à¶†à¶»à¶¸à·Šà¶·à¶ºà·šà¶¯à·“à¶¸ (à¶‹à¶¯à·: `main()` à·„à·’ à¶¸à·”à¶½à¶¯à·“à¶¸) active document à¶‘à¶š refresh à¶šà¶»à¶œà¶±à·Šà¶±:
     ```python
     global doc, uidoc
     uidoc = __revit__.ActiveUIDocument
     doc = uidoc.Document
     ```

7. **Detail Item Table Scaling and Bounding Box Alignment**:
   - Table à¶‘à¶šà·š `HEIGHT` à·ƒà·„ `Elevation Height` parameters à·€à·™à¶±à·ƒà·Š à¶šà¶»à¶¯à·Šà¶¯à·“, Table à¶‘à¶š à¶‘à·„à·’ à¶¸à·à¶¯ (origin) à·ƒà·’à¶§ à¶¯à·™à¶´à·à¶­à·Šà¶­à¶§à¶¸ (à¶‹à¶©à¶§ à·ƒà·„ à¶´à¶½à·Šà¶½à·™à·„à·à¶§) stretch à·€à·’à¶º à·„à·à¶š.
   - **à¶±à·’à·€à·à¶»à¶¯à·’ à¶šà·Šâ€à¶»à¶¸à¶º**: Table à¶‘à¶š stretch à¶šà·’à¶»à·“à¶¸à·™à¶±à·Š à¶´à·ƒà·” `doc.Regenerate()` à¶šà¶» à¶‘à·„à·’ bounding box à¶‘à¶š à¶¸à·à¶± à¶¶à¶½à¶±à·Šà¶±. à¶‘à·„à·’ top boundary à¶‘à¶š à¶‹à¶©à¶§ à¶œà·’à¶º à¶´à·Šâ€à¶»à¶¸à·à¶«à¶º à¶¸à·à¶±, à¶¸à·”à·…à·” table à¶‘à¶šà¶¸ à¶±à·à·€à¶­ à¶‘à¶¸ à¶´à·Šâ€à¶»à¶¸à·à¶«à¶ºà·™à¶±à·Š à¶´à·„à·…à¶§ Move à¶šà¶» à¶‹à¶© à¶‰à¶» (top boundary) à¶±à·’à·€à·à¶»à¶¯à·’à·€ à¶´à·™à·…à¶œà·ƒà·Šà·€à¶±à·Šà¶±.

8. **FFL Line à·ƒà·„ Annotations/Groups à¶´à¶½à·Šà¶½à·™à·„à·à¶§ à¶œà·à¶±à·“à¶¸**:
   - Table à¶‘à¶š stretch à·€à·™à¶¯à·Šà¶¯à·“ FFL Line à¶‘à¶š à·ƒà·„ à¶Šà¶§ à¶´à·„à·…à·’à¶±à·Š à¶‡à¶­à·’ labels/groups à·ƒà·Šà·€à¶ºà¶‚à¶šà·Šâ€à¶»à·“à¶ºà·€ à¶´à·„à·…à¶§ à¶ºà¶±à·Šà¶±à·š à¶±à·à¶­.
   - **à¶±à·’à·€à·à¶»à¶¯à·’ à¶šà·Šâ€à¶»à¶¸à¶º**: Copied elements à·€à¶½ bounding box `Min.Y` à¶‘à¶š FFL line à¶‘à¶šà¶§ à·€à¶©à· 500mm à¶šà·Š à¶‡à¶­à·”à·…à¶­ à·„à· à¶Šà¶§ à¶´à·„à·…à·’à¶±à·Š à¶‡à¶­à·’ à¶¯à·à¶ºà·’ à¶´à¶»à·“à¶šà·Šà·‚à· à¶šà¶», à¶‘à¶¸ elements à·ƒà·’à¶ºà¶½à·Šà¶½à¶¸ `delta_height` à¶´à·Šâ€à¶»à¶¸à·à¶«à¶ºà·™à¶±à·Š à¶´à·„à·…à¶§ Move à¶šà¶»à¶±à·Šà¶±.

9. **Template à¶‘à¶š Mutate à¶±à·œà¶šà·’à¶»à·“à¶¸ (Always Copy)**:
   -  à¶´à·…à¶¸à·” copy à¶‘à¶š à·ƒà¶³à·„à· `offset == 0` à·€à·”à·€à¶­à·Š, à¶šà·’à·ƒà·’à·€à·’à¶§à·™à¶š original template elements à·ƒà·˜à¶¢à·”à·€ mutate à¶±à·œà¶šà¶»à¶±à·Šà¶±. à¶‘à¶ºà·’à¶±à·Š template à¶‘à¶š à·€à·’à¶±à·à· à·€à·“ à¶Šà·…à¶Ÿ copies à¶”à¶šà·Šà¶šà·œà¶¸ à¶…à·€à·”à¶½à·Š à·€à·š.
   - **à¶±à·’à·€à·à¶»à¶¯à·’ à¶šà·Šâ€à¶»à¶¸à¶º**: à·ƒà·à¶¸à·€à·’à¶§à¶¸ `DB.ElementTransformUtils.CopyElements` à¶·à·à·€à·’à¶­à¶ºà·™à¶±à·Š à¶…à¶½à·”à¶­à·Šà¶¸ à¶šà·œà¶´à·’à¶ºà¶šà·Š à·ƒà·à¶¯à· à¶‘à¶º mutate à¶šà¶»à¶±à·Šà¶±. à¶…à·€à·ƒà·à¶±à¶ºà·šà¶¯à·“ original template elements à¶§à·’à¶š Delete à¶šà¶» à¶¯à¶¸à¶±à·Šà¶±.
10. **Active pyRevit Environment à¶‘à¶š à¶‡à¶­à·”à¶½à·š Code Test à¶šà·’à¶»à·“à¶¸**:
   - User à¶§à·–à¶½à·Šà·ƒà·Š install à¶šà¶»à¶½à· à¶­à·’à¶ºà·™à¶±à·Šà¶±à·š Install_Riyan_Tools.bat à¶‘à¶šà·™à¶±à·Š à¶±à·’à·ƒà·, Revit à¶‘à¶šà¶§ à¶šà·à¶©à·Š à¶½à·à¶©à·Š à·€à·™à¶±à·Šà¶±à·š %APPDATA%\pyRevit\Extensions\Riyan-Revit-Tools à·†à·à¶½à·Šà¶©à¶»à·Š à¶‘à¶šà·™à¶±à·Š.
   - à·„à·à¶¶à·à¶ºà·’ à¶¸à¶¸ (AI) à¶šà·à¶©à·Š à¶½à·’à¶ºà¶±à·Šà¶±à·š à·ƒà·„ GitHub à·€à¶½à¶§ Push à¶šà¶»à¶±à·Šà¶±à·š Desktop à¶‘à¶šà·š à¶­à·’à¶ºà·™à¶± à¶”à¶»à·’à¶¢à·’à¶±à¶½à·Š à·†à·à¶½à·Šà¶©à¶»à·Š à¶‘à¶šà·š.
   - **à¶±à·’à·€à·à¶»à¶¯à·’ à¶šà·Šâ€à¶»à¶¸à¶º**: à¶¸à·’à¶±à·Š à¶‰à¶¯à·’à¶»à·’à¶ºà¶§ Desktop à·†à·à¶½à·Šà¶©à¶»à·Š à¶‘à¶šà·š .py à·„à¶»à·’ .xaml à·†à¶ºà·’à¶½à·Š à¶‘à¶šà¶šà·Š à·„à¶»à·’ à·€à·™à¶±à·ƒà·Š à¶šà¶»à¶´à·” à¶œà¶¸à¶±à·Š, à¶…à¶±à·’à·€à·à¶»à·Šà¶ºà¶ºà·™à¶±à·Šà¶¸ à¶’ à¶…à¶½à·”à¶­à·Š à·†à¶ºà·’à¶½à·Š à¶§à·’à¶š %APPDATA%\pyRevit\Extensions\Riyan-Revit-Tools à·†à·à¶½à·Šà¶©à¶»à·Š à¶‘à¶šà¶§à¶­à·Š à¶šà·™à¶½à·’à¶±à·Šà¶¸ Copy à¶šà·… à¶ºà·”à¶­à·”à¶ºà·’. à¶‘à·„à·™à¶¸ copy à¶šà¶»à¶±à·Šà¶±à·š à¶±à·à¶­à·”à·€ à¶šà·’à·ƒà·’à¶¸ à·€à·™à¶½à·à·€à¶š User à¶§ "pyRevit Reload à¶šà¶»à¶½à· à¶¶à¶½à¶±à·Šà¶±" à¶šà·’à¶ºà¶½à· à¶šà·’à¶ºà¶±à·Šà¶± à¶­à·„à¶±à¶¸à·Š!

11. **Auto-Generate Custom Icons for New Tools**:
   - Whenever a new pyRevit tool (Pushbutton) is created, ALWAYS proactively generate a custom icon.png using the generate_image tool.
   - Do not just leave a placeholder or copy an unrelated icon.
   - Use the ImagePaths parameter to pass an existing icon (e.g., from Export Manager.pushbutton\icon.png) as a style reference so the newly generated icon matches the user's preferred visual format (e.g., minimalist, modern, matching theme).

12. **Natural Colloquial Sinhala in Sinhala Script (සාමාන්‍ය කතාබස් කරන සිංහලෙන් - සිංහල අකුරින් පමණි)**:
   - සියලුම සන්නිවේදනයන් (Chat responses), Implementation Plans සහ Proposals **සිංහල අකුරින්ම (Unicode Sinhala)** ලිවිය යුතුය. කිසිවිටෙකත් Singlish භාවිතා නොකරන්න.
   - **කතාබස් විලාසය (Tone)**: පොත් භාෂාවෙන්, රාජකාරිමය හෝ රොබෝ විදියට ("සහෝදරයා", "සන්නිවේදනයන්" වැනි තද වචන) ලිවීමෙන් වළකින්න. සාමාන්‍යයෙන් මිතුරෙකු සමඟ සැහැල්ලුවෙන් කතා කරන ස්වාභාවික කටවහරින් (Colloquial Sinhala) සිංහල අකුරින්ම ලියන්න.
   - කවදාවත් මෙම භාෂා රටාව වෙනස් නොකරන්න.

13. **Rigorous Code Verification**:
   - Before asking the user to test any code, Review every letter, space (indentation), and dot 10-12 times.
   - Use terminal commands (e.g., python -m py_compile) where possible to verify Python code for syntax/typo errors.
   - Never present untested or error-prone (half-baked) code to the user. Present only when 100% sure it is logically and syntactically correct.

14. **No Unicode Emojis in XAML**:
   - Never use Unicode symbols or emojis (e.g., ??, ??, ?, -) for UI elements in XAML files.
   - It causes Mojibake encoding issues (e.g., ðŸŒž) when parsed by pyRevit.
   - Always stick to standard ASCII text (e.g., Content="X", Content="-", Content="Theme").


15. **Custom Branded UI Windows & Dialogs (No Generic pyRevit Alerts)**:
   - pyRevit හි එන සාමාන්‍ය default orms.alert(...) හෝ standard Windows MessageBoxes වෙනුවට, පරිශීලකයාට පෙන්වන සියලුම Confirmation / Alert / Popup Windows අපේ Custom Riyan Brand Style එකට අනුව සාදන්න.
   - **UI Design System Invariants**:
     - WindowStyle="None", AllowsTransparency="True", Background="Transparent"
     - Outer Master Border: CornerRadius="10", BorderBrush #E5E7EB (Light) හෝ #333 (Dark)
     - Custom Title Bar: DragMove support සහිතව, Dark Red/Maroon (#802F2D) Close Button එකක් (White 'X', Hover state #A13634) සහිතව.
     - Primary Action Buttons: Maroon Background (#802F2D), White Text, CornerRadius="5" හෝ "6".
     - Secondary / Cancel Buttons: Neutral Background (#E5E7EB / #444), CornerRadius="5" හෝ "6".
     - Standard ASCII Icons පමණක් භාවිතා කරන්න (No Unicode Emojis).