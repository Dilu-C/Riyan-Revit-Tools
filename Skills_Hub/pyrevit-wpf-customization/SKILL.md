---
name: pyrevit-wpf-customization
description: Comprehensive engineering guide, architectural patterns, and troubleshooting rules for developing pyRevit WPF UI extensions, custom dialogs, DataGrid sorting, and the Export Manager suite using IronPython.
---

# pyRevit WPF & Export Manager Master Engineering Guide

This master skill contains the unified architectural rules, bug fixes, and critical lessons learned from developing high-performance WPF extensions for pyRevit and the Export Manager plugin suite.

---

## 1. WPF DataGrid Sorting with IronPython Objects
**Issue**: WPF `DataGrid` automatic column sorting fails silently or throws exceptions when `ItemsSource` is bound to a plain Python list (e.g., `SheetViewModel` instances) because WPF's reflection (`PropertyDescriptor`) cannot resolve dynamic properties on IronPython objects natively.
**Solution**:
- Catch the `Sorting` event manually (via `PreviewMouseLeftButtonUp` on headers or `Sorting="Grid_Sorting"` in XAML).
- Use a Python `lambda` to sort the underlying list:
  ```python
  items.sort(key=lambda x: getattr(x, prop_name, ''), reverse=is_descending)
  ```
- Force a UI refresh by explicitly clearing and reassigning the items:
  ```python
  new_list = [x for x in items]
  self.DataGrid.ItemsSource = None
  self.DataGrid.ItemsSource = new_list
  ```

---

## 2. Hit-Testing on Transparent WPF Elements
**Issue**: Clicks on transparent areas of a button, custom header template, or canvas do not register in WPF.
**Solution**: Always wrap the content inside a `<Border Background="Transparent">`. An explicit transparent background ensures the WPF hit-testing engine registers the click across the entire element geometry rather than letting it pass through.

---

## 3. IronPython 2.7 Syntax & Indentation Strictness
**Issue**: When programmatically editing or writing Python scripts for pyRevit, indentation errors are catastrophic.
**Rules**:
- Never mix tabs and spaces. Use 4 spaces exclusively.
- Ensure module-level comments (`# ---`), functions, or classes are preceded by an empty line if they follow an indented block, otherwise IronPython throws `unexpected token '<dedent>'` runtime exceptions.

---

## 4. XAML Events and pyRevit's XamlReader
**Issue**: pyRevit uses a custom XAML loader for `forms.WPFWindow` (`xaml.load_xaml`) that uses regex to strip certain events before loading, but it is inconsistent. Assigning events like `SelectionChanged="MethodName"` or `Click="MethodName"` directly in XAML will often result in a `XamlParseException` because the compiled code-behind assembly is missing.
**Solution**:
- Never declare `SelectionChanged` or custom UI events directly in XAML.
- Bind them in Python at the end of `__init__`:
  ```python
  self.MyElement.SelectionChanged += self.MyMethod
  ```
- Use a custom initialization flag (e.g., `self._init_done = True`) at the very end of `__init__` and check `if not getattr(self, '_init_done', False): return` inside event handlers to avoid `AttributeError` from native WPF properties like `self.IsLoaded` not being ready during startup.

---

## 5. File Encoding & PowerShell UTF-8 Corruption (Mojibake Guardrail)
**Issue**: Using native PowerShell 5.1 commands like `Get-Content` and `Set-Content` to patch files containing UTF-8 characters (like Unicode UI icons, emojis, or accents) will silently read them as ANSI and corrupt them (Mojibake), even if `-Encoding UTF8` is specified for saving.
**Solution**:
- Do not use standard PowerShell `Set-Content` for file patching if the file contains UTF-8 characters.
- Always rely on Python scripts with explicit `open(..., encoding='utf-8')` to perform safe string replacements, or strictly use .NET classes (`[System.IO.File]::ReadAllText(path, [System.Text.Encoding]::UTF8)`) in PowerShell.

---

## 6. Safe Fuzzy Matching for XAML Edits
**Issue**: Automated string replacement tools can disastrously corrupt XAML layouts if the target string (e.g. a generic `Button.Style` or `StackPanel`) looks structurally identical to another section.
**Solution**: Always include highly specific context (like unique `x:Name="..."`, parent container tags, or distinctive comments) in the search block to anchor the replacement safely.

---

## 7. Preventing Zombie / Hidden Dialogs in Revit
**Issue**: Using pyRevit's standard `forms.alert` at the very end of a heavy threading/export process often causes the alert to spawn invisibly behind the Revit main window, effectively freezing Revit because the modal dialog is trapped in the background.
**Solution**:
- Avoid standard `forms.alert` for the final "Export Complete" message.
- Create a custom WPF `Window` (e.g. `CustomExportCompletedWindow`) loaded via `xaml.load_xaml`.
- Set `self.Topmost = True` and use borderless styling (`WindowStyle="None"`, `AllowsTransparency="True"`) to prevent Windows from mishandling the Z-order.
- Add `MouseLeftButtonDown` event tied to `self.DragMove()` so the user can interact with and close the frameless window safely.

---

## 8. Window Focus & Topmost Protection During Batch Runs
**Issue**: When opening background Revit documents (`app.OpenDocumentFile`) or running export loops (PDF/DWG/NWC/IFC), Revit's native engine forces its main window to activate, which causes tool windows to fall behind and hide.
**Solution**:
- Force `self.Topmost = True` and call `self.Activate()` immediately when long-running/batch operations or exports begin.
- Always reset `self.Topmost = False` in a `finally:` block when the operation finishes or cancels.

---

## 9. File Locking Protection & Rename Prompts
**Issue**: When overwriting files (especially PDFs), if the user or another viewer has the destination file open in Adobe Acrobat or Bluebeam Revu, Revit's `doc.Export` will silently fail or crash.
**Solution**:
- Implement a `check_and_resolve_filename(folder, filename, ext)` method before exporting.
- **Lock Check**: Use `open(full_path, 'a')` to test for `IOError`.
- **Prompt**: If locked, alert the user with options `["Try Again", "Rename", "Skip"]`. If not locked but exists, offer `["Replace", "Rename", "Skip"]`.
- Use recursion with `forms.ask_for_string` to continually check the new name if the user selects "Rename".

---

## 10. Dual Themes (Light & Dark) Implementation
**Issue**: Standard pyRevit tools often use a hardcoded dark theme. We require modern theme adaptiveness.
**Solution**:
- **XAML Files**: Maintain two versions of the UI: `ExportUI.xaml` (Dark) and `ExportUI_Light.xaml` (Light), or dynamic resource dictionaries.
- **Settings Toggle**: The `OptionsWindow` should include RadioButtons (`RbThemeDark`, `RbThemeLight`) to toggle the theme.
- **Python Loading**: In `script.py` within `Form.__init__`, check `settings.get("theme", "Dark")` and dynamically load the respective XAML file. Ensure elements (like logos or custom icons) that depend on background colors are adjusted appropriately.

---

## 11. Modern UI Gradients for Progress & Status
**Issue**: Standard DataGrid text columns and ProgressBars look dated and lack visual feedback.
**Solution**:
- **ProgressBar**: Use `<ProgressBar.Foreground><LinearGradientBrush ...></ProgressBar.Foreground>` instead of flat colors.
- **DataGrid**: Replace `<DataGridTextColumn>` with `<DataGridTemplateColumn>`. Place a `<Border>` inside the CellTemplate and use `<DataTemplate.Triggers>` binding to the `Status` property (e.g. "Done", "Exporting...", "Error") to change the Border's `Background` to a full `LinearGradientBrush`.

---

## 12. Combined PDF Routing & Naming Builder Blueprint
- **Routing**: Remove separate UI for Combined PDF folder selection. Route the combined PDF directly to the main `Export Directory`. If "Save and split files by file format" is checked, append `\PDF` to the path.
- **Naming Builder**: Support `is_combined=True` which loads `doc.ProjectInformation` parameters instead of `Sheet` parameters.
- **Dynamic Previews**: Implement `update_combined_filename_preview()` method to parse `self.active_combined_scheme_parts` and dynamically generate the combined filename using `doc.ProjectInformation`.
- **Window Resizing**: Restructure root `<Grid>` to use `RowDefinitions` (`Auto`, `*`, `Auto`) so the inner DataGrid expands, and include `<ResizeGrip>` for borderless drag-resizing.
- **Persistent Setups**: Ensure `CmbPdfSetup` and `CmbDwgSetup` selections are persistently saved inside `naming_settings.json` under `profile_settings`.