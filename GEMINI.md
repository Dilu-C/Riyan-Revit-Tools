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
   - pyRevit වල Cached Engines ක්‍රියාත්මක වන විට, module-level variables (උදා: `doc = revit.doc` හෝ `uidoc = revit.uidoc`) පරණ document එකටම ලොක් වී පැවතිය හැක.
   - **නිවැරදි ක්‍රමය**: සැමවිටම main execution එක ආරම්භයේදීම (උදා: `main()` හි මුලදීම) active document එක refresh කරගන්න:
     ```python
     global doc, uidoc
     uidoc = __revit__.ActiveUIDocument
     doc = uidoc.Document
     ```

7. **Detail Item Table Scaling and Bounding Box Alignment**:
   - Table එකේ `HEIGHT` සහ `Elevation Height` parameters වෙනස් කරද්දී, Table එක එහි මැද (origin) සිට දෙපැත්තටම (උඩට සහ පල්ලෙහාට) stretch විය හැක.
   - **නිවැරදි ක්‍රමය**: Table එක stretch කිරීමෙන් පසු `doc.Regenerate()` කර එහි bounding box එක මැන බලන්න. එහි top boundary එක උඩට ගිය ප්‍රමාණය මැන, මුළු table එකම නැවත එම ප්‍රමාණයෙන් පහළට Move කර උඩ ඉර (top boundary) නිවැරදිව පෙළගස්වන්න.

8. **FFL Line සහ Annotations/Groups පල්ලෙහාට ගැනීම**:
   - Table එක stretch වෙද්දී FFL Line එක සහ ඊට පහළින් ඇති labels/groups ස්වයංක්‍රීයව පහළට යන්නේ නැත.
   - **නිවැරදි ක්‍රමය**: Copied elements වල bounding box `Min.Y` එක FFL line එකට වඩා 500mm ක් ඇතුළත හෝ ඊට පහළින් ඇති දැයි පරීක්ෂා කර, එම elements සියල්ලම `delta_height` ප්‍රමාණයෙන් පහළට Move කරන්න.

9. **Template එක Mutate නොකිරීම (Always Copy)**:
   -  පළමු copy එක සඳහා `offset == 0` වුවත්, කිසිවිටෙක original template elements සෘජුව mutate නොකරන්න. එයින් template එක විනාශ වී ඊළඟ copies ඔක්කොම අවුල් වේ.
   - **නිවැරදි ක්‍රමය**: සැමවිටම `DB.ElementTransformUtils.CopyElements` භාවිතයෙන් අලුත්ම කොපියක් සාදා එය mutate කරන්න. අවසානයේදී original template elements ටික Delete කර දමන්න.
10. **Active pyRevit Environment එක ඇතුලේ Code Test කිරීම**:
   - User ටූල්ස් install කරලා තියෙන්නේ Install_Riyan_Tools.bat එකෙන් නිසා, Revit එකට කෝඩ් ලෝඩ් වෙන්නේ %APPDATA%\pyRevit\Extensions\Riyan-Revit-Tools ෆෝල්ඩර් එකෙන්.
   - හැබැයි මම (AI) කෝඩ් ලියන්නේ සහ GitHub වලට Push කරන්නේ Desktop එකේ තියෙන ඔරිජිනල් ෆෝල්ඩර් එකේ.
   - **නිවැරදි ක්‍රමය**: මින් ඉදිරියට Desktop ෆෝල්ඩර් එකේ .py හරි .xaml ෆයිල් එකක් හරි වෙනස් කරපු ගමන්, අනිවාර්යයෙන්ම ඒ අලුත් ෆයිල් ටික %APPDATA%\pyRevit\Extensions\Riyan-Revit-Tools ෆෝල්ඩර් එකටත් කෙලින්ම Copy කළ යුතුයි. එහෙම copy කරන්නේ නැතුව කිසිම වෙලාවක User ට "pyRevit Reload කරලා බලන්න" කියලා කියන්න තහනම්!
