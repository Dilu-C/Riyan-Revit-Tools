---
trigger: always_on
description: Mandatory rules for Revit WPF/WinForms UI design, window focus retention, and dialog formatting.
---

# Revit UI & Window Lifecycle Guardrails

## 1. Window Focus & Topmost Protection (Zero Window Drop Guardrail)
- **Prevent Revit Focus Stealing**: When opening background Revit documents (`app.OpenDocumentFile`) or running export loops (PDF/DWG/NWC/IFC), Revit's native engine forces its main window to activate, which causes tool windows to fall behind and hide.
- **Mandatory Topmost Lock During Execution**:
  - The tool window MUST set `self.Topmost = True` and call `self.Activate()` immediately when long-running/batch operations or exports begin.
  - Call `self.Activate()` whenever background documents are opened or in dispatcher event loops (`do_events`).
  - Always reset `self.Topmost = False` in a `finally:` block when the operation finishes or cancels.
  - Set `Topmost = True` on completion popups/dialogs so they appear clearly in front of the user.
- **Win32 HWND Ownership**: Always hook `SourceInitialized` on WPF windows to assign Win32 owner (`Interop.WindowInteropHelper(self).Owner = revit_handle`) once the HWND is fully created.

## 2. Windows Folder Picker & Dialog Guardrails
- **No Long Text in FolderBrowserDialog Description**: Never assign long descriptive sentences to `dlg.Description` in `System.Windows.Forms.FolderBrowserDialog`. Windows Forms confines this text to a narrow 150px bottom label, squishing it into an ugly multiline clump.
- **Enable Title Bar Mode**: Always check and enable:
  ```python
  if hasattr(dlg, "UseDescriptionForTitle"):
      dlg.UseDescriptionForTitle = True
      dlg.Description = title
  ```
- **Clean Dialog Interior**: If title bar mode is not available, leave `dlg.Description = ""` or keep it under 3 words so the interior of the dialog remains 100% clean, spacious, and uncluttered.

## 3. WPF Button ControlTemplate & Padding Rules
- **Mandatory TemplateBinding on Border**: Whenever defining custom WPF button templates (`PrimaryBtn`, `SecondaryBtn`), the inner container `Border` MUST include `Padding="{TemplateBinding Padding}"`. Omitting this attribute causes all button padding to be silently ignored by WPF.
- **Consistent Typography & Height**: All toolbar buttons must share consistent typography (e.g. `FontSize="12"`, `FontWeight="SemiBold"`) and matching heights (e.g. `Height="32"`).

## 4. Toolbar Button Widths & Visual Harmony
- **No Compressed Buttons**: Toolbar buttons must never collapse tightly against text. Always provide either an explicit matching width (e.g. `Width="95"`, `Width="100"`) or a safe minimum width with breathing room (`MinWidth="110"` with `Padding="10,0"`).
- **Dynamic Content Safety**: If a button's content changes dynamically (e.g. showing a selected folder name or profile), always use `MinWidth` to prevent the toolbar from jumping or clipping.

## 5. Strict User Selection & Checkbox State Guardrail (Zero Unwanted Processing)
- **Strict WPF Checkbox Evaluation**: WPF `CheckBox.IsChecked` is a nullable boolean (`True`, `False`, `None`). Never evaluate checkboxes loosely with `!= False` or `if chk.IsChecked:`. In IronPython/Python, `None != False` evaluates to `True`, allowing indeterminate/unticked items to execute. Always evaluate strictly:
  ```python
  if chk and chk.IsChecked == True:
      # Explicitly selected by user
  ```
- **Absolute Respect for User Intent**: If an item is unticked, unchecked, or deselected by the user, it MUST be 100% strictly bypassed.
- **Zero Side-Effects for Unselected Items**: NEVER create output folders, temporary directories, transmittal entries, or open background documents for items that are not explicitly checked.
- **Early Skip Enforcement**: Always enforce strict selection checks at both the UI collection stage and the start of the processing loop before any folder creation or document loading occurs.

## 6. Theme-Adaptive Modal Dialogs & Text Contrast (Dark & Light Themes)
- **Zero OS-Default Chrome for Sub-Dialogs**: Any custom sub-dialog or popup (e.g. Create Profile, Confirm Delete, Conflict Overwrite, Options, Renaming) must NEVER use default OS window frames. Always use borderless custom chrome (`WindowStyle="None"`, `AllowsTransparency="False"` or `"True"` with rounded border) accompanied by a sleek custom draggable title bar and close button (`✕`).
- **Mandatory Text Contrast Across Themes**:
  - In **Light Theme**: Backgrounds must be bright/white (`#FFFFFF` or `#F3F3F3`), and all labels, textboxes, radio buttons, and buttons MUST explicitly set dark text (`#101828` or `#111111`). Never allow washed-out grey or default white text on light backgrounds.
  - In **Dark Theme**: Backgrounds must be dark (`#161616` or `#1E1E1E`), and text colors MUST be light/white (`#FFFFFF` or `#E0E0E0`).
  - Inputs (TextBox) and RadioButtons must always specify theme-aware background, foreground, and border brushes.

### 6.1 Zero Static Foregrounds in Theme-Adaptive Windows (Strict Dynamic Theme Propagation)
- **Zero Hardcoded Foreground in XAML**: In any dual-theme or theme-adaptive WPF window, NEVER hardcode static text colors (e.g. `Foreground="#E4E4E7"`, `Foreground="#FFFFFF"`, `Foreground="#F4F4F5"`) directly on controls (`ListBox`, `TextBlock`, `RadioButton`, `ComboBox`, `TextBox`).
- **DynamicResource Binding or Deep Visual Tree Propagation**:
  1. All text elements MUST bind via `{DynamicResource TextPrimary}`, `{DynamicResource TextSecondary}`, `{DynamicResource SurfaceBg}`, OR
  2. The window's `apply_theme()` engine MUST explicitly traverse and update the `Foreground` on every single child container (`LstCategories`, `TitleBar`, `DisciplineBar`, `TxtResultsCount`, `PanelDetail`, etc.).
- **Strict Light Theme Contrast Mandate**:
  - In **Light Theme**:
    - Primary text MUST be `#0F172A` (Deep Slate Black).
    - Secondary text / categories / labels MUST be `#334155` / `#475569` (Dark Slate).
    - Unselected ListBox items and RadioButtons MUST have dark text (`#0F172A`).
    - Under NO circumstances may white or light gray text appear on white/slate backgrounds.

## 7. Destructive Action & Overwrite Protection (Zero Unwanted Deletion Guardrail)
- **Mandatory Confirmation on Destructive Actions**: Never execute destructive operations (e.g. deleting a Naming Profile, deleting a Sheet Set, deleting sheets/files) directly upon a single click.
- **Custom Warning Confirmation Dialog**: Always present a polished, theme-adaptive confirmation dialog displaying:
  - An Amber/Red warning icon.
  - Clear text indicating the specific item name being affected and warning that the action cannot be undone.
  - Explicit action button (e.g. `Delete` with danger/accent style) and `Cancel` (secondary neutral style) button.
  - The action MUST only proceed if the user explicitly confirms via the action button.
- **File Overwrite Conflict Handling**: When exporting files that already exist in the target folder, provide a sleek dialog with options:
  - `Replace` / `OK`: Overwrite only this file.
  - `Replace All` / `All OK`: Overwrite this and all subsequent files in the current batch.
  - `Cancel`: Abort the export operation.

## 8. WPF Concentric TitleBar & Close Button Chrome (Zero Corner Bleed Guardrail)
- **Zero Square Corner Bleeding**: In any borderless window (`WindowStyle="None" AllowsTransparency="True"`) with a rounded outer `Border CornerRadius="R"`, internal header containers (TitleBar) MUST NOT be raw unrounded Grids.
- **Concentric Header Border**: Always wrap the TitleBar in a `<Border CornerRadius="R-1, R-1, 0, 0">` so its background color curves strictly within the outer border and never pokes out as sharp/square corners.
- **Mandatory Close Button Template**: The top-right Close (`✕`) button must NEVER use OS default button styles (which render an ugly light-blue square box `#BEE6FD` on hover). It MUST define a custom `ControlTemplate` with:
  - Concentric corner radius matching the window top-right corner: `<Border CornerRadius="0, R-1, 0, 0">`.
  - Modern hover trigger (e.g. background `#DC2626` and foreground `White`).

## 9. Studio White Canvas for CAD/BIM Thumbnails (Zero Inverted Linework Invisibility)
- **Linework Visibility Mandate**: Autodesk Revit family thumbnails and preview bitmaps frequently contain black wireframe lines (`RGB 0,0,0`), 2D annotations, and black text on transparent backgrounds.
- **Zero Black-on-Black Viewports**: NEVER set thumbnail container backgrounds (`ThumbnailBg`) to dark/black gradients (`#161619`, `#25252A`) in Dark Theme. Doing so renders black linework completely invisible, creating empty dark squares.
- **Universal White Studio Canvas**: CAD/BIM thumbnail containers MUST always use a clean, bright Light/White Studio Canvas (`#FFFFFF` or soft off-white `#F8FAFC`) with a subtle border (`#3F3F46`), so all black lines, 2D symbols, and true shaded 3D colors pop with 100% crystal clarity across BOTH Dark and Light themes.

## 10. Zero Hardcoded Version Strings in UI (Dynamic Release Binding)
- **Zero Static Version Text in Dialogs**: Never hardcode version strings (e.g. `V2.5.0`) in window titles, header text, or update badges in popups (like "What's New", About, Splash).
- **Dynamic Runtime Binding**: Dialogs must always dynamically read the active release version from `version.txt` at runtime and format placeholders (e.g. `{VERSION}`) so that UI text always matches the real installed release bit-for-bit.

## 12. Riyan Executive Slate Theme Standard (Zero "Thani Black" / Stark Pitch Black)
- **Zero Pitch Black Backgrounds**: Never use harsh pitch black (`#000000`, `#111111`) as the main window background. Riyan's signature aesthetic uses a balanced Soft Slate Charcoal:
  - **Window Background**: `#2D2D30` (Executive Slate Charcoal)
  - **Container / Group Background**: `#1E1E1E` (Dark Charcoal)
  - **Row / Item Card Background**: `#252528` (Card Surface)
  - **Borders & Separators**: `#3F3F46` (Clean Balanced Slate Border)
  - **Primary Brand Accent**: `#C0272D` (Crimson Red)
  - **Secondary Brand Accent**: `#C8922A` (Signature Gold / Amber)
- **Mandatory Explicit Text Foreground**: In custom WPF list items or dynamic rows, never omit `Foreground` on `TextBlock` or `CheckBox`. Default OS foreground is black (`#000000`), which causes invisible text on dark backgrounds. Always explicitly bind/set:
  - Primary text: `#FFFFFF` (100% Crisp White in Dark Theme) / `#111827` (Light Theme)
  - Secondary / path text: `#D1D5DB` (High-contrast Slate in Dark Theme) / `#374151` (Light Theme)

## 13. WPF Button Custom ControlTemplate for Hover Protection (Zero Icon/Text Washout)
- **Prevent Aero Overlay Washout**: Default WPF buttons apply a light-blue/white gradient overlay on hover that makes white text and Unicode emoji/icons (e.g., `🚀`, `☼`, `✕`) completely vanish.
- **Mandatory ControlTemplate on Action Buttons**:
  - Always assign an explicit `ControlTemplate` with `Border` + `ContentPresenter` and `Padding="{TemplateBinding Padding}"`.
  - Provide explicit mouse-over triggers (`<Trigger Property="IsMouseOver" Value="True">`) adjusting background (e.g. Crimson Hover `#D32F2F`) while keeping foreground and content 100% visible.
- **Matrix Terminal Console Standard**:
  - Console viewer text must use vibrant terminal green (`#22C55E` in dark mode, `#16A34A` / `#4ADE80` in light mode) over dark monospace container (`#121214`), preserving instant diagnostic clarity.

## 14. Universal Modal Hierarchy & Escape Key Dismissal Invariant (Zero Multi-Window Drop on ESC)
- **Hierarchical ESC Dismissal (එකින් එක පිළිවෙළට වැසීමේ නීතිය)**: 
  Parent window එකක් මත child modal window එකක් හෝ popup dialog එකක් විවෘතව ඇති විට, පරිශීලකයා `Escape` (ESC) යතුර එබූ විට වැසිය යුත්තේ **ඉදිරියෙන්ම ඇති Child Dialog එක පමණි**. Parent window එක කිසිසේත්ම නොවැසී 100% ක් විවෘතව පැවතිය යුතුය.
- **Mandatory `e.Handled = True` on ESC**: 
  ඕනෑම child modal, popup, හෝ sub-dialog එකක `PreviewKeyDown` / `KeyDown` handler තුළ `Key.Escape` හසුරුවන විට, `self.Close()` කැඳවීමට පෙර හෝ පසුව අනිවාර්යයෙන්ම **`e.Handled = True`** ලෙස සලකුණු කළ යුතුය. එමඟින් Key Event එක parent window එකට කාන්දු වීම 100% ක් වළක්වයි.
- **Parent Active-Child Protection Guard**: 
  Parent window එකක `PreviewKeyDown` තුළ `Key.Escape` හසුරුවන විට, යම් child dialog එකක් active වී ඇත්නම් parent window එක close නොවී `e.Handled = True` කර event එක terminate කළ යුතුය.
- **Explicit WPF Window Ownership**: 
  Child window එකක් පෙන්වීමට පෙර සැමවිටම `child_win.Owner = parent_win` ලෙස explicit owner කෙනෙකු ලබා දිය යුතු අතර `ShowDialog()` හරහා modal hierarchy එක සුරක්ෂිත කළ යුතුය.

## 15. Ribbon Button Titles & pyRevit Tooltip Guardrail (Zero Ribbon Bloat Guardrail / බොත්තම් නම් කෙටියෙන් තැබීමේ නීතිය)
- **Zero Unprompted Button Title Alterations**: Tooltips (`tooltip:`) එක් කිරීමේදී හෝ සංස්කරණය කිරීමේදී, කිසිම හේතුවක් මත `bundle.yaml` හි ඇති `title:` attribute එක වෙනස් නොකළ යුතුය. pyRevit තුළ `title:` යනු Ribbon එකේ සෘජුවම දිස්වන බොත්තම් නාමයයි (Button Label).
- **Strict Ribbon Compactness (බොත්තම් නම් කෙටියෙන් පමණක් තැබීම)**: Ribbon බොත්තම් නම් සැමවිටම ඉතා කෙටි, පැහැදිලි සහ සංයුක්ත විය යුතුය (උදා: `Add`, `Remove`, `Map`, `Data`, `Table`, `Dims`, `About`). ඒවාට දිගු විස්තරාත්මක වාක්‍ය හෝ නාම එක් කිරීමෙන් stacks සහ panels පළල වී මුළු Ribbon එකම විකෘති වේ.
- **Tooltips Belong in `tooltip:` Only**: මෙවලම පිළිබඳ සියලු උපදෙස්, භාවිතයන් සහ විස්තර අනිවාර්යයෙන්ම ලිවිය යුත්තේ `tooltip: >-` property එක තුළ පමණි. බොත්තමේ `title:` එකට කිසිදු අතගැසීමක් නොකළ යුතුය.

## 16. Ribbon Tooltips & MediaElement Pitfall Guardrail (Zero Black Box Tooltips / Dropdown වලට PNG පමණක් භාවිත කිරීමේ නීතිය)
- **WPF MediaElement Failure in Popups/Pulldowns**: In Autodesk Revit Ribbon (AdWindows), WPF `MediaElement` (`tooltip.mp4`) fails to receive the `Loaded` event when hovered inside a Pulldown/Dropdown Menu (`RibbonMenuButton`) or nested popups. Because `Loaded` never fires, `sender.Play()` is never invoked, causing the tooltip to render as an ugly, solid black box (`#000000`).
- **Mandatory High-Res PNG for Pulldown & Dropdown Items**:
  - Any button placed inside a Pulldown, Dropdown, Menu, or Sub-stack MUST NEVER use `tooltip.mp4`.
  - Always use a high-resolution, side-by-side Before/After image (`tooltip.png`) rendered via WPF `DrawingVisual`.
  - `tooltip.png` loads via `System.Windows.Controls.Image` with 0ms latency, 100% crispness, and zero risk of rendering a black box across all Revit versions.
  - Delete or exclude `tooltip.mp4` from these directories so pyRevit never discovers or loads the video element.
- **Top-Level Button Video Privilege**: `tooltip.mp4` is reserved strictly for Top-Level buttons sitting directly on ribbon panels where the WPF visual tree triggers `MediaElement.Loaded` cleanly.


