# Revit API & pyRevit Internal Best Practices

1. **Legend Component Copying**: CopyElements between different Legend Views fails silently if a translation transform is passed in the same method call. Duplicate base view, copy elements within duplicated view using DB.Transform.Identity, move with MoveElements, delete template elements.
2. **ScheduleSheetInstances on Titleblocks**: Titleblocks contain Revision Schedules (no filter support). Always verify sched.Definition.CategoryId to filter out Revision Schedules.
3. **Schedule Bounding Boxes**: Place schedule, commit SubTransaction, doc.Regenerate() before using BoundingBox.
4. **Python Scoping Trap (UnboundLocalError)**: Avoid local module imports inside except blocks. Use global imports at the top of file.
5. **List Instantiation for ElementIds**: Explicitly construct System.Collections.Generic.List[DB.ElementId]().
6. **Active Document Caching**: Refresh active document in main execution (`global doc, uidoc; uidoc = __revit__.ActiveUIDocument; doc = uidoc.Document`).
7. **Detail Item Table Scaling and Bounding Box Alignment**: Measure top boundary shift after doc.Regenerate() and adjust table position.
8. **FFL Line & Annotations**: Move related annotations down by delta_height.
9. **Template Mutating**: Never mutate original template elements directly; copy first.
10. **Revit 2024-2027+ ElementId Compatibility**: Never call `elem.Id.IntegerValue` directly as Revit 2025, 2026, and 2027 deprecate/remove it in favor of Int64 (`elem.Id.Value`). Always use a universal helper:
    ```python
    def get_elem_id_val(eid):
        if not eid: return 0
        return eid.Value if hasattr(eid, "Value") else eid.IntegerValue
    ```
11. **No Unicode Emojis in XAML**: Avoid direct raw unicode emojis in WPF XAML.
12. **Never Query `PrintManager` or `ViewSheetSetting` on Background Documents**: Querying `PrintManager` or `ViewSheetSetting` during background document inspection triggers external print drivers and third-party add-in hooks (e.g. DiRoots ProSheets, Bluebeam PDF compatibility checks), displaying blocking modal TaskDialogs. Always query Sheet Sets directly via `DB.FilteredElementCollector(doc).OfClass(DB.ViewSheetSet)` without touching `PrintManager`.
13. **Mandatory Loop Cancellation Invariant**: Every batch loop iterating over multiple background Revit documents MUST check for user cancellation (`if getattr(self, '_cancel_export', False): break`) and pump UI messages (`do_events`) on every single file iteration to guarantee that the user can immediately stop the process without hanging Revit.
14. **Mandatory Desktop-to-AppData Extension Synchronization (Dual-Tree Guardrail)**: The active development repository is located at `Desktop\Riyan-Revit-Tools`, while Revit executes pyRevit extensions from `AppData\Roaming\pyRevit\Extensions\Riyan-Revit-Tools`. Every modification made to scripts, XAML, or config files in `Desktop\Riyan-Revit-Tools` MUST be mirrored/synced immediately to `AppData\Roaming\pyRevit\Extensions\Riyan-Revit-Tools` in the same turn before notifying the user or requesting testing. Never ask the user to test in Revit or report that a feature is ready without verifying that file hashes in AppData match the Desktop repository.
15. **pyRevit WPF Window Event Binding & Keyboard Focus Invariants**:
    - **Explicit Root Window Event Binding**: In `forms.WPFWindow`, event attributes on the root `<Window>` tag in XAML (e.g. `PreviewKeyDown`, `Closing`, `Closed`) are NOT automatically wired by `XamlReader.Load()`. They MUST always be explicitly hooked in code in `__init__` (e.g. `self.PreviewKeyDown += self.Window_PreviewKeyDown`).
    - **Focusable Custom Rows**: For custom row containers (`Border`, `Grid`) inside ScrollViewers/StackPanels, always set `Focusable = True` and call `.Focus()` on mouse click so keyboard events (Spacebar, Escape, Enter) route correctly and are not captured by background buttons.
    - **Reliable Hit-Testing**: Containers or cells designed to capture clicks across their full area must use `Background="#01000000"` (not `Background="Transparent"`) to ensure 100% consistent WPF mouse hit-testing.
16. **Pre-Release Compilation & Extension Startup Guardrail (Zero-Broken-Release Mandate)**:
    - **Python 3 / CPython Syntax Audit Before Release**: Revit 2025, 2026, and 2027 execute pyRevit under CPython 3 (e.g. CPY3123) and .NET 8. In Python 3, keywords like `None`, `True`, `False`, etc. are reserved tokens; dot-access like `obj.None` causes an immediate fatal `SyntaxError`. Before declaring any update, release, or git commit ready for testing or deployment to the team, the agent MUST run a full compilation audit across ALL `.py` files in the repository using the pyRevit CPython compiler (`& "C:\Program Files\pyRevit-Master\bin\cengines\CPY3123\python.exe" -c "import py_compile..."`).
    - **Fail-Safe Startup Protection**: Code in `startup.py` or extension initializer scripts MUST NEVER fail or throw unhandled compile-time or runtime errors. Any syntax or runtime error in `startup.py` prevents pyRevit from loading the entire extension, completely removing the extension ribbon tab from Revit. Startup UI notifications (such as toasts) must be isolated with safe attribute access (e.g., `getattr(WindowStyle, 'None')`) and guarded defensively so the extension tab always loads unconditionally.
    - **Full XAML XML Validation**: All newly introduced or modified `.xaml` files must be parsed with `[xml](Get-Content <file> -Raw)` to ensure well-formed XML before testing or release.
17. **Revit ViewSheetSet Manipulation Invariants (`ViewSheetSetting.Save()` vs `SaveAs()`)**:
    - **Always Set PrintRange to Select First**: Before querying or modifying `print_mgr.ViewSheetSetting`, always set `print_mgr.PrintRange = DB.PrintRange.Select`. Omitting this triggers Revit API `InvalidOperationException`.
    - **Never Delete Existing Sets via `doc.Delete` for Updates**: To update an existing `ViewSheetSet`, NEVER delete its element ID with `doc.Delete(s.Id)`. Doing so desynchronizes `PrintManager`'s internal set cache and causes subsequent calls to fail.
    - **Proper Update vs Create Pattern**:
      - **Existing Set**: Assign `vss.CurrentViewSheetSet = target_vss`, assign `vss.CurrentViewSheetSet.Views = view_set`, and call `vss.Save()`.
      - **New Set**: Assign `vss.CurrentViewSheetSet = vss.InSession`, assign `vss.CurrentViewSheetSet.Views = view_set`, and call `vss.SaveAs(new_name)`.
    - **No False Success on Transaction Failure**: Never catch a failed Revit transaction and proceed to display "successfully updated" dialogs. If the transaction rolls back, notify the user with the actual exception and never discard the in-memory user selection.
18. **Zero Regression & Core Feature Preservation Guardrail (කලින් හදපු වැඩ කැඩීම වැළැක්වීමේ නීතිය)**:
    - Whenever modifying scripts, refactoring UI, or adding new features, the agent MUST NOT break, mutate, or degrade existing core functions (Sheet Set saving/loading, Selection logic, Naming profiles, Export engines).
    - Code changes must be surgically scoped to avoid unintended side effects on adjacent handlers.
    - Any silent exception swallows (`except: pass`) in core save/write operations are strictly prohibited.
19. **Revit 2027 .NET 8 & Multi-Version Forward-Compatibility Mandate**:
    - **.NET 8 Runtime Strictness**: Revit 2025, 2026, and 2027 operate on Microsoft .NET 8.0 runtime. Never use deprecated assemblies, legacy Windows Forms hacks, or unmanaged Win32 hooks that fail in .NET Core.
    - **Zero Deprecated Units (ForgeTypeId)**: Never use `DisplayUnitType` or `UnitType` enums. Always use `UnitTypeId` / `SpecTypeId` for parameter and document units across Revit 2022-2027+.
    - **TitleBlock Query Invariant**: Never query sheet title blocks using `OwnedByView(sheet.Id)`. Always use the universal multi-version constructor: `DB.FilteredElementCollector(doc, sheet.Id).OfCategory(DB.BuiltInCategory.OST_TitleBlocks)`.
    - **Universal Multi-Tier Date & Parameter Extraction**: Parameters across Revit 2021-2027 must always be queried with both `p.AsString()` and `p.AsValueString()`. Date extraction must scan Sheet instance parameters, Title Block instance & symbol parameters, Revision dates, and Project Information case-insensitively with dummy placeholder filtering.
20. **Revit Link Graphics & View Template Control Invariant**:
    - **Revit Links Cannot be Overridden via Right-Click "By Element" for Colors/Patterns**: In Revit, canvas right-click (`Override Graphics in View > By Element`) on a Revit Link does NOT support surface patterns or color fills (it only supports Halftone and Transparency). True graphic overrides on links must strictly be managed through `Visibility/Graphic Overrides (VG/VV) -> Revit Links` tab (using `By linked view` or `Custom > Model Categories`), or directly inside a **View Template**'s `V/G Overrides Revit Links`.
    - **View Template Primacy & Detection**: If a view is governed by a View Template (`view.ViewTemplateId != DB.ElementId.InvalidElementId`), direct view-level link overrides are disabled or ignored. All link graphic overrides must be read from and applied directly to the View Template (`doc.GetElement(view.ViewTemplateId)` as `DB.View`).
    - **Strict Pre-Advising Verification**: Every UI instruction and workflow advice given to the user regarding Revit element manipulation must be strictly verified against actual Autodesk Revit UI and API capabilities.
