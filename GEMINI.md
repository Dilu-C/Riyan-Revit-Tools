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