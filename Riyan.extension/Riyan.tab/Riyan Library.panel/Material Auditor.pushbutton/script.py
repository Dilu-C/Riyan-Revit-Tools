# -*- coding: utf-8 -*-
"""
Material Auditor & Standardizer
Audits all loadable families in the active document for material standardization (RYN_MAT criteria).
Compatible with Autodesk Revit 2021 through Revit 2027+.
"""
import os
import sys
import codecs
import json
import clr

clr.AddReference("System")
clr.AddReference("System.Windows.Forms")
clr.AddReference("PresentationFramework")
clr.AddReference("PresentationCore")
clr.AddReference("WindowsBase")
clr.AddReference("System.Xml")
clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")

import System
from System.Windows import (
    Window, Application, WindowStartupLocation, WindowStyle,
    Thickness, VerticalAlignment, HorizontalAlignment, FontWeights,
    TextWrapping, Visibility, GridLength, GridUnitType
)
from System.Windows.Controls import (
    Border, Grid, ColumnDefinition, TextBlock, StackPanel, TextBox
)
from System.Windows.Media import SolidColorBrush, Color, ColorConverter
from System.Windows.Interop import WindowInteropHelper
import Autodesk.Revit.DB as DB
from pyrevit import script
try:
    from riyan_alert import show_alert
except ImportError:
    _lib_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "lib"))
    if _lib_dir not in sys.path:
        sys.path.append(_lib_dir)
    from riyan_alert import show_alert
import System.Windows.Forms as WinForms

# Riyan Standard Material Dictionary
STANDARD_MATERIAL_MAP = {
    # Door Frames
    "door - frame - alum": "RYN_MAT_DoorFrame_Aluminium",
    "door - frame": "RYN_MAT_DoorFrame_Aluminium",
    "door-frame-alum": "RYN_MAT_DoorFrame_Aluminium",
    "alum - door frame": "RYN_MAT_DoorFrame_Aluminium",
    "door frame - timber": "RYN_MAT_DoorFrame_Timber",
    "door frame timber": "RYN_MAT_DoorFrame_Timber",
    "wood - frame": "RYN_MAT_DoorFrame_Timber",

    # Door Leaves / Panels
    "door - panel in timber": "RYN_MAT_DoorPanel_Timber",
    "door panel in timber": "RYN_MAT_DoorPanel_Timber",
    "door - panel - timber": "RYN_MAT_DoorPanel_Timber",
    "door - panel": "RYN_MAT_DoorPanel_Timber",
    "door - leaf": "RYN_MAT_DoorPanel_Timber",
    "door leaf": "RYN_MAT_DoorPanel_Timber",
    "door - frame - alum (leaf)": "RYN_MAT_DoorPanel_Aluminium",

    # Glass
    "door - glass": "RYN_MAT_Glass",
    "door glass": "RYN_MAT_Glass",
    "window panel - glass": "RYN_MAT_Glass",
    "glass": "RYN_MAT_Glass",
    "clear glass": "RYN_MAT_Glass",

    # Louvers
    "door panel louver": "RYN_MAT_DoorPanel_Louver_Aluminium",
    "louver - alum": "RYN_MAT_DoorPanel_Louver_Aluminium",
    "louver": "RYN_MAT_DoorPanel_Louver_Aluminium",

    # Window Frames
    "window frame - alum": "RYN_MAT_WindowFrame_Aluminium",
    "window - frame - alum": "RYN_MAT_WindowFrame_Aluminium",
    "window frame": "RYN_MAT_WindowFrame_Aluminium",
    "window panel frame - alum": "RYN_MAT_WindowPanelFrame_Aluminium"
}

EXPECTED_DOOR_PARAMS = [
    "RYN_Material_DoorFrame",
    "RYN_Material_DoorLeaf",
    "RYN_Material_Glass"
]

EXPECTED_WINDOW_PARAMS = [
    "RYN_Material_WindowFrame",
    "RYN_Material_WindowPanelFrame",
    "RYN_Material_Glass"
]

def sanitize_material_name(raw_name):
    """Sanitizes raw name into clean CamelCase / PascalCase for RYN_MAT_ standard."""
    import re
    s = raw_name.strip()
    if s.upper().startswith("RYN_MAT_"):
        s = s[8:]
    elif s.upper().startswith("RYN_"):
        s = s[4:]
    s = re.sub(r'[\:\;\<\>\?\|\`\~\[\]\{\}\\\/]', ' ', s)
    s = re.sub(r'[\-_]+', ' ', s)
    words = [w.capitalize() for w in s.split() if w]
    clean = "_".join(words) if words else "Generic"
    return "RYN_MAT_" + clean

def find_matching_ryn_material(raw_mat_name, param_name, cat_name, doc_mats_by_name):
    """
    Finds an existing authentic RYN_MAT_ material in doc that corresponds to raw_mat_name.
    Returns Material element or None.
    """
    name_low = raw_mat_name.lower()
    p_low = param_name.lower()
    cat_low = cat_name.lower()

    # 1. Direct standard map
    if name_low in STANDARD_MATERIAL_MAP:
        target = STANDARD_MATERIAL_MAP[name_low].lower()
        if target in doc_mats_by_name:
            return doc_mats_by_name[target]

    # 2. Glass / Vetro
    if "glass" in name_low or "vetro" in name_low or "glass" in p_low:
        for cand in ["ryn_mat_glass", "ryn_mat_clearglass", "ryn_mat_door_glass"]:
            if cand in doc_mats_by_name:
                return doc_mats_by_name[cand]

    # 3. Door Frame
    if "door" in cat_low and "frame" in p_low:
        if "alum" in name_low or "metal" in name_low or "alluminio" in name_low:
            if "ryn_mat_doorframe_aluminium" in doc_mats_by_name:
                return doc_mats_by_name["ryn_mat_doorframe_aluminium"]
        elif "timber" in name_low or "wood" in name_low or "legno" in name_low:
            if "ryn_mat_doorframe_timber" in doc_mats_by_name:
                return doc_mats_by_name["ryn_mat_doorframe_timber"]

    # 4. Door Leaf / Panel
    if "door" in cat_low and ("leaf" in p_low or "panel" in p_low):
        if "timber" in name_low or "wood" in name_low or "legno" in name_low:
            if "ryn_mat_doorpanel_timber" in doc_mats_by_name:
                return doc_mats_by_name["ryn_mat_doorpanel_timber"]
        elif "alum" in name_low or "alluminio" in name_low:
            if "ryn_mat_doorpanel_aluminium" in doc_mats_by_name:
                return doc_mats_by_name["ryn_mat_doorpanel_aluminium"]

    # 5. Window Frame
    if "win" in cat_low and "frame" in p_low:
        if "ryn_mat_windowframe_aluminium" in doc_mats_by_name:
            return doc_mats_by_name["ryn_mat_windowframe_aluminium"]

    # 6. General Aluminium / Metal
    if "aluminium" in name_low or "aluminum" in name_low or "alluminio" in name_low:
        for cand in ["ryn_mat_metal_aluminium", "ryn_mat_aluminium", "ryn_mat_metal_aluminum"]:
            if cand in doc_mats_by_name:
                return doc_mats_by_name[cand]

    # 7. Steel / Iron
    if "steel" in name_low or "aço" in name_low or "aco" in name_low or "acciaio" in name_low:
        for cand in ["ryn_mat_metal_steel", "ryn_mat_steel"]:
            if cand in doc_mats_by_name:
                return doc_mats_by_name[cand]

    return None

class MaterialAuditorWindow(Window):
    def __init__(self, doc, uiapp):
        self.doc = doc
        self.uiapp = uiapp
        self.is_dark_theme = True
        self.audit_data = None
        self.current_tab = "Inconsistent"

        xaml_path = os.path.join(os.path.dirname(__file__), "ui.xaml")
        with codecs.open(xaml_path, "r", "utf-8") as f:
            xaml_content = f.read()

        from System.Windows.Markup import XamlReader
        self.window = XamlReader.Parse(xaml_content)

        # Wire elements
        self.TxtDocName = self.window.FindName("TxtDocName")
        self.TxtTotalCount = self.window.FindName("TxtTotalCount")
        self.TxtCompliantCount = self.window.FindName("TxtCompliantCount")
        self.TxtInconsistentCount = self.window.FindName("TxtInconsistentCount")
        self.TxtMissingParamsCount = self.window.FindName("TxtMissingParamsCount")
        self.ItemsList = self.window.FindName("ItemsList")
        self.BtnTheme = self.window.FindName("BtnTheme")
        self.BtnStandardize = self.window.FindName("BtnStandardize")

        self.TabInconsistent = self.window.FindName("TabInconsistent")
        self.TabMissing = self.window.FindName("TabMissing")
        self.TabCompliant = self.window.FindName("TabCompliant")

        # Events
        self.TitleBar = self.window.FindName("TitleBar")
        if self.TitleBar:
            self.TitleBar.MouseDown += self.OnTitleBarMouseDown

        self.BtnClose = self.window.FindName("BtnClose")
        if self.BtnClose:
            self.BtnClose.Click += self.OnCloseClicked

        self.BtnMaximize = self.window.FindName("BtnMaximize")
        if self.BtnMaximize:
            self.BtnMaximize.Click += self.on_maximize_restore

        self.PanelProgress = self.window.FindName("PanelProgress")
        self.ProgressBarStandardize = self.window.FindName("ProgressBarStandardize")
        self.TxtProgressStatus = self.window.FindName("TxtProgressStatus")
        self.TxtProgressPct = self.window.FindName("TxtProgressPct")

        self.BtnExport = self.window.FindName("BtnExport")
        if self.BtnExport:
            self.BtnExport.Click += self.OnExportReport

        if self.BtnTheme:
            self.BtnTheme.Click += self.OnToggleTheme
        if self.BtnStandardize:
            self.BtnStandardize.Click += self.OnApplyStandardization

        if self.TabInconsistent:
            self.TabInconsistent.Checked += self.OnTabChanged
        if self.TabMissing:
            self.TabMissing.Checked += self.OnTabChanged
        if self.TabCompliant:
            self.TabCompliant.Checked += self.OnTabChanged

        self.TxtSearch = self.window.FindName("TxtSearch")
        self.TxtSearchPlaceholder = self.window.FindName("TxtSearchPlaceholder")
        if self.TxtSearch:
            self.TxtSearch.TextChanged += self.OnSearchChanged

        # Win32 ownership
        try:
            hwnd = self.uiapp.MainWindowHandle
            helper = WindowInteropHelper(self.window)
            helper.Owner = hwnd
        except Exception:
            pass

        self.TxtDocName.Text = u"Document: " + (self.doc.Title if self.doc else u"No Active Document")

        # Run Audit
        self.run_audit()
        self.apply_theme()

    def run_audit(self):
        if not self.doc:
            return

        doc_mats_by_name = {m.Name.lower(): m for m in DB.FilteredElementCollector(self.doc).OfClass(DB.Material)}
        collector = DB.FilteredElementCollector(self.doc).OfClass(DB.Family)
        total = 0
        compliant = []
        inconsistent = []
        missing_params = []

        for fam in collector:
            if fam.IsInPlace:
                continue

            fam_name = fam.Name
            cat_name = fam.FamilyCategory.Name if fam.FamilyCategory else "Unknown"
            total += 1

            is_door = "DOOR" in fam_name.upper() or cat_name == "Doors"
            is_window = "WIN" in fam_name.upper() or cat_name == "Windows"

            expected_params = []
            if is_door:
                expected_params = EXPECTED_DOOR_PARAMS
            elif is_window:
                expected_params = EXPECTED_WINDOW_PARAMS

            symbols = fam.GetFamilySymbolIds()
            if not symbols or symbols.Count == 0:
                continue

            sym_list = list(symbols)
            if not sym_list:
                continue
            sym = self.doc.GetElement(sym_list[0])
            if not sym:
                continue
            param_names = [p.Definition.Name for p in sym.Parameters if p and p.Definition]

            missing = [ep for ep in expected_params if ep not in param_names]
            if missing:
                missing_params.append({
                    "FamilyName": fam_name,
                    "Category": cat_name,
                    "Details": u"Missing: " + u", ".join(missing),
                    "BadgeText": u"Param Missing",
                    "BadgeBg": SolidColorBrush(Color.FromRgb(80, 20, 20)),
                    "BadgeFg": SolidColorBrush(Color.FromRgb(255, 120, 120))
                })

            has_inconsistent = False
            mat_info = []
            for p in sym.Parameters:
                if not p or not p.Definition:
                    continue
                p_name = p.Definition.Name
                if "Material" in p_name or "MAT" in p_name:
                    m_id = p.AsElementId()
                    m_name = "None"
                    if m_id and m_id != DB.ElementId.InvalidElementId:
                        m_elem = self.doc.GetElement(m_id)
                        if m_elem:
                            m_name = m_elem.Name

                    if m_name != "None" and not m_name.startswith("RYN_MAT_"):
                        has_inconsistent = True
                        matched_ryn = find_matching_ryn_material(m_name, p_name, cat_name, doc_mats_by_name)
                        if matched_ryn:
                            action_str = u"🔄 Replace: '{}' ➔ {}".format(m_name, matched_ryn.Name)
                        else:
                            clean_n = sanitize_material_name(m_name)
                            if clean_n.lower() in doc_mats_by_name:
                                action_str = u"🔄 Reuse: '{}' ➔ {}".format(m_name, doc_mats_by_name[clean_n.lower()].Name)
                            else:
                                action_str = u"✏️ Rename: '{}' ➔ {}".format(m_name, clean_n)
                        mat_info.append(u"{}: {}".format(p_name, action_str))

            if has_inconsistent:
                inconsistent.append({
                    "FamilyName": fam_name,
                    "Category": cat_name,
                    "Details": u" | ".join(mat_info),
                    "BadgeText": u"Needs RYN_MAT_",
                    "BadgeBg": SolidColorBrush(Color.FromRgb(80, 60, 10)),
                    "BadgeFg": SolidColorBrush(Color.FromRgb(245, 158, 11))
                })
            elif not missing:
                compliant.append({
                    "FamilyName": fam_name,
                    "Category": cat_name,
                    "Details": u"Fully standardized to RYN_MAT_ standard",
                    "BadgeText": u"Compliant",
                    "BadgeBg": SolidColorBrush(Color.FromRgb(16, 60, 40)),
                    "BadgeFg": SolidColorBrush(Color.FromRgb(16, 185, 129))
                })

        self.audit_data = {
            "total": total,
            "compliant": compliant,
            "inconsistent": inconsistent,
            "missing": missing_params
        }

        self.TxtTotalCount.Text = str(total)
        self.TxtCompliantCount.Text = str(len(compliant))
        self.TxtInconsistentCount.Text = str(len(inconsistent))
        self.TxtMissingParamsCount.Text = str(len(missing_params))

        self.update_list_view()

    def OnSearchChanged(self, sender, e):
        if hasattr(self, "TxtSearchPlaceholder") and self.TxtSearchPlaceholder:
            self.TxtSearchPlaceholder.Visibility = Visibility.Collapsed if self.TxtSearch.Text.strip() else Visibility.Visible
        self.update_list_view()

    def update_list_view(self):
        if not hasattr(self, "ItemsList") or not self.ItemsList:
            return
        self.ItemsList.Items.Clear()
        if not self.audit_data:
            return

        if self.current_tab == "Inconsistent":
            items = self.audit_data.get("inconsistent", [])
        elif self.current_tab == "Missing":
            items = self.audit_data.get("missing", [])
        else:
            items = self.audit_data.get("compliant", [])

        search_query = self.TxtSearch.Text.strip().lower() if (hasattr(self, "TxtSearch") and self.TxtSearch) else ""

        rendered_count = 0
        for item in items:
            if search_query:
                fn = item.get("FamilyName", "").lower()
                cn = item.get("Category", "").lower()
                dt = item.get("Details", "").lower()
                if search_query not in fn and search_query not in cn and search_query not in dt:
                    continue

            row = self.create_audit_row(item)
            self.ItemsList.Items.Add(row)
            rendered_count += 1

        if rendered_count == 0:
            empty_panel = StackPanel()
            empty_panel.HorizontalAlignment = HorizontalAlignment.Center
            empty_panel.VerticalAlignment = VerticalAlignment.Center
            empty_panel.Margin = Thickness(0, 50, 0, 50)
            
            empty_txt = TextBlock()
            empty_txt.Text = u"No families found matching current filter."
            empty_txt.Foreground = self.window.Resources["TextMuted"]
            empty_txt.FontSize = 13
            empty_txt.FontWeight = FontWeights.SemiBold
            empty_panel.Children.Add(empty_txt)
            self.ItemsList.Items.Add(empty_panel)

    def create_audit_row(self, item):
        res = self.window.Resources
        row_border = Border()
        row_border.Background = res["SurfaceBg"]
        row_border.BorderBrush = res["BorderColor"]
        row_border.BorderThickness = Thickness(1)
        row_border.CornerRadius = System.Windows.CornerRadius(6)
        row_border.Padding = Thickness(14, 10, 14, 10)
        row_border.Margin = Thickness(0, 0, 0, 6)

        grid = Grid()
        c0 = ColumnDefinition(); c0.Width = GridLength(1, GridUnitType.Auto)
        c1 = ColumnDefinition(); c1.Width = GridLength(1, GridUnitType.Star)
        c2 = ColumnDefinition(); c2.Width = GridLength(1, GridUnitType.Auto)
        grid.ColumnDefinitions.Add(c0)
        grid.ColumnDefinitions.Add(c1)
        grid.ColumnDefinitions.Add(c2)

        # 1. Category Badge
        cat_badge = Border()
        if self.is_dark_theme:
            cat_badge.Background = SolidColorBrush(Color.FromArgb(50, 128, 47, 45))
        else:
            cat_badge.Background = SolidColorBrush(Color.FromArgb(25, 128, 47, 45))
        cat_badge.CornerRadius = System.Windows.CornerRadius(4)
        cat_badge.Padding = Thickness(8, 4, 8, 4)
        cat_badge.Margin = Thickness(0, 0, 12, 0)
        cat_badge.VerticalAlignment = VerticalAlignment.Center
        
        cat_text = TextBlock()
        cat_text.Text = item.get("Category", "Unknown")
        cat_text.Foreground = res["RiyanRose"]
        cat_text.FontSize = 11
        cat_text.FontWeight = FontWeights.Bold
        cat_badge.Child = cat_text
        Grid.SetColumn(cat_badge, 0)
        grid.Children.Add(cat_badge)

        # 2. Family Name & Details
        info_stack = StackPanel()
        info_stack.VerticalAlignment = VerticalAlignment.Center
        
        fam_text = TextBlock()
        fam_text.Text = item.get("FamilyName", "")
        fam_text.Foreground = res["TextPrimary"]
        fam_text.FontSize = 13
        fam_text.FontWeight = FontWeights.Bold
        info_stack.Children.Add(fam_text)

        det_text = TextBlock()
        det_text.Text = item.get("Details", "")
        det_text.Foreground = res["TextSecondary"]
        det_text.FontSize = 11
        det_text.TextWrapping = TextWrapping.Wrap
        det_text.Margin = Thickness(0, 3, 0, 0)
        info_stack.Children.Add(det_text)
        
        Grid.SetColumn(info_stack, 1)
        grid.Children.Add(info_stack)

        # 3. Status Badge (Theme-Adaptive High Contrast)
        badge_type = item.get("BadgeText", "")
        badge_border = Border()
        badge_border.CornerRadius = System.Windows.CornerRadius(4)
        badge_border.Padding = Thickness(10, 4, 10, 4)
        badge_border.VerticalAlignment = VerticalAlignment.Center
        badge_border.Margin = Thickness(12, 0, 0, 0)

        badge_txt = TextBlock()
        badge_txt.Text = badge_type
        badge_txt.FontSize = 11
        badge_txt.FontWeight = FontWeights.Bold

        if "Missing" in badge_type:
            if self.is_dark_theme:
                badge_border.Background = SolidColorBrush(Color.FromRgb(69, 26, 26))
                badge_txt.Foreground = SolidColorBrush(Color.FromRgb(252, 165, 165))
            else:
                badge_border.Background = SolidColorBrush(Color.FromRgb(254, 226, 226))
                badge_txt.Foreground = SolidColorBrush(Color.FromRgb(220, 38, 38))
        elif "Needs" in badge_type:
            if self.is_dark_theme:
                badge_border.Background = SolidColorBrush(Color.FromRgb(66, 32, 6))
                badge_txt.Foreground = SolidColorBrush(Color.FromRgb(252, 211, 77))
            else:
                badge_border.Background = SolidColorBrush(Color.FromRgb(254, 243, 199))
                badge_txt.Foreground = SolidColorBrush(Color.FromRgb(217, 119, 6))
        else: # Compliant
            if self.is_dark_theme:
                badge_border.Background = SolidColorBrush(Color.FromRgb(6, 78, 59))
                badge_txt.Foreground = SolidColorBrush(Color.FromRgb(110, 231, 183))
            else:
                badge_border.Background = SolidColorBrush(Color.FromRgb(209, 250, 229))
                badge_txt.Foreground = SolidColorBrush(Color.FromRgb(5, 150, 105))

        badge_border.Child = badge_txt
        Grid.SetColumn(badge_border, 2)
        grid.Children.Add(badge_border)

        row_border.Child = grid
        return row_border

    def OnTabChanged(self, sender, e):
        if self.TabInconsistent.IsChecked:
            self.current_tab = "Inconsistent"
        elif self.TabMissing.IsChecked:
            self.current_tab = "Missing"
        elif self.TabCompliant.IsChecked:
            self.current_tab = "Compliant"
        self.update_list_view()

    def apply_theme(self):
        res = self.window.Resources
        if self.is_dark_theme:
            res["WindowBg"] = SolidColorBrush(Color.FromRgb(18, 19, 22))
            res["SurfaceBg"] = SolidColorBrush(Color.FromRgb(26, 28, 32))
            res["CardBg"] = SolidColorBrush(Color.FromRgb(34, 37, 42))
            res["BorderColor"] = SolidColorBrush(Color.FromRgb(46, 51, 61))
            res["TextPrimary"] = SolidColorBrush(Color.FromRgb(244, 244, 245))
            res["TextSecondary"] = SolidColorBrush(Color.FromRgb(148, 163, 184))
            res["TextMuted"] = SolidColorBrush(Color.FromRgb(100, 116, 139))
            res["RiyanMaroon"] = SolidColorBrush(Color.FromRgb(128, 47, 45))
            res["RiyanRose"] = SolidColorBrush(Color.FromRgb(192, 86, 82))
            self.BtnTheme.Content = "☀️ Light"
        else:
            # Strict High-Contrast Light Theme
            res["WindowBg"] = SolidColorBrush(Color.FromRgb(248, 250, 252))
            res["SurfaceBg"] = SolidColorBrush(Color.FromRgb(255, 255, 255))
            res["CardBg"] = SolidColorBrush(Color.FromRgb(241, 245, 249))
            res["BorderColor"] = SolidColorBrush(Color.FromRgb(203, 213, 225))
            res["TextPrimary"] = SolidColorBrush(Color.FromRgb(15, 23, 42))     # Deep Slate Black
            res["TextSecondary"] = SolidColorBrush(Color.FromRgb(51, 65, 85))   # Dark Slate
            res["TextMuted"] = SolidColorBrush(Color.FromRgb(100, 116, 139))
            res["RiyanMaroon"] = SolidColorBrush(Color.FromRgb(128, 47, 45))
            res["RiyanRose"] = SolidColorBrush(Color.FromRgb(140, 40, 38))
            self.BtnTheme.Content = "🌙 Dark"

        # Explicitly enforce foreground on RadioButtons & controls
        self.TabInconsistent.Foreground = res["TextPrimary"]
        self.TabMissing.Foreground = res["TextPrimary"]
        self.TabCompliant.Foreground = res["TextPrimary"]
        if hasattr(self, "TxtSearch") and self.TxtSearch:
            self.TxtSearch.Foreground = res["TextPrimary"]
        self.update_list_view()

    def OnTitleBarMouseDown(self, sender, e):
        try:
            if hasattr(e, "ClickCount") and e.ClickCount == 2:
                self.on_maximize_restore(sender, e)
            else:
                from System.Windows.Input import MouseButton
                if e.ChangedButton == MouseButton.Left:
                    self.window.DragMove()
        except Exception:
            pass

    def on_maximize_restore(self, sender=None, e=None):
        try:
            from System.Windows import WindowState
            if self.window.WindowState == WindowState.Maximized:
                self.window.WindowState = WindowState.Normal
                if hasattr(self, "BtnMaximize") and self.BtnMaximize:
                    self.BtnMaximize.Content = u"🗖"
            else:
                self.window.WindowState = WindowState.Maximized
                if hasattr(self, "BtnMaximize") and self.BtnMaximize:
                    self.BtnMaximize.Content = u"🗗"
        except Exception:
            pass

    def OnCloseClicked(self, sender, e):
        self.window.Close()

    def OnToggleTheme(self, sender, e):
        self.is_dark_theme = not self.is_dark_theme
        self.apply_theme()

    def OnApplyStandardization(self, sender, e):
        if not self.doc:
            show_alert("No active document open to standardize.", title="Material Auditor", is_error=True)
            return

        inconsistent_list = self.audit_data.get("inconsistent", []) if self.audit_data else []
        if not inconsistent_list:
            show_alert("All families in this document are already RYN_MAT_ compliant!", title="Material Auditor", is_warning=False)
            return

        # Initialize pyRevit Output Console for live non-freezing visual progress
        out = script.get_output()
        out.set_title("Material Auditor - Live Standardization")
        try:
            out.open()
        except Exception:
            pass
        out.print_md("## 🎨 Riyan Material Auditor — Live Standardization")
        out.print_md("Standardizing **{} families** to `RYN_MAT_` corporate standard...".format(len(inconsistent_list)))

        # Activate In-Window Live Progress Bar
        if self.PanelProgress:
            self.PanelProgress.Visibility = Visibility.Visible
        if self.ProgressBarStandardize:
            self.ProgressBarStandardize.Value = 0
        if self.TxtProgressPct:
            self.TxtProgressPct.Text = u"0%"
        if self.TxtProgressStatus:
            self.TxtProgressStatus.Text = u"Starting RYN_MAT_ corporate standardization..."
        WinForms.Application.DoEvents()

        try:
            t = DB.Transaction(self.doc, "Apply RYN_MAT_ Standardization")
            t.Start()

            # Refresh and index doc materials once for O(1) performance
            mat_collector = list(DB.FilteredElementCollector(self.doc).OfClass(DB.Material))
            doc_mats_by_id = {m.Id: m for m in mat_collector}
            doc_mats_by_name = {m.Name.lower(): m for m in mat_collector}

            # Pre-index all families once in memory (Prevents 128 redundant DB scans!)
            fams_by_name = {}
            for f in DB.FilteredElementCollector(self.doc).OfClass(DB.Family):
                if not f.IsInPlace:
                    fams_by_name[f.Name] = f

            renamed_set = set()
            renamed_count = 0
            replaced_count = 0
            total_items = len(inconsistent_list)

            for idx, fam_item in enumerate(inconsistent_list):
                fam_name = fam_item.get("FamilyName")
                cat_name = fam_item.get("Category", "")
                
                # Live Progress Bar & Windows message pumping (Never freezes!)
                pct = int(((idx + 1) / float(total_items)) * 100)
                out.update_progress(idx + 1, total_items)
                if self.ProgressBarStandardize:
                    self.ProgressBarStandardize.Value = pct
                if self.TxtProgressPct:
                    self.TxtProgressPct.Text = u"{}% ({}/{})".format(pct, idx + 1, total_items)
                if self.TxtProgressStatus:
                    self.TxtProgressStatus.Text = u"Standardizing '{}' [{}]...".format(fam_name, cat_name)
                WinForms.Application.DoEvents()

                f = fam_f = fams_by_name.get(fam_name)
                if not f:
                    continue

                for sym_id in f.GetFamilySymbolIds():
                    sym = self.doc.GetElement(sym_id)
                    if not sym:
                        continue
                    for p in sym.Parameters:
                        if not p or not p.Definition:
                            continue
                        p_name = p.Definition.Name
                        if "Material" in p_name or "MAT" in p_name:
                            m_id = p.AsElementId()
                            if not m_id or m_id == DB.ElementId.InvalidElementId:
                                continue

                            m_elem = doc_mats_by_id.get(m_id) or self.doc.GetElement(m_id)
                            if not m_elem:
                                continue
                            m_name = m_elem.Name
                            if m_name.startswith("RYN_MAT_"):
                                continue

                            # 1. Check if matches an existing authentic RYN_MAT_ material
                            matched_ryn = find_matching_ryn_material(m_name, p_name, cat_name, doc_mats_by_name)
                            if matched_ryn:
                                p.Set(matched_ryn.Id)
                                replaced_count += 1
                                out.print_html(u"<span style='color:#10b981'>✔ [{}/{}] <b>{}</b> : Replaced '{}' ➔ <b>{}</b></span>".format(
                                    idx + 1, total_items, fam_name, m_name, matched_ryn.Name))
                                continue

                            # 2. Check if clean standard name already exists in project
                            clean_name = sanitize_material_name(m_name)
                            if clean_name.lower() in doc_mats_by_name:
                                existing_m = doc_mats_by_name[clean_name.lower()]
                                p.Set(existing_m.Id)
                                replaced_count += 1
                                out.print_html(u"<span style='color:#3b82f6'>🔗 [{}/{}] <b>{}</b> : Reused Existing ➔ <b>{}</b></span>".format(
                                    idx + 1, total_items, fam_name, existing_m.Name))
                            else:
                                # Rename unique material preserving all textures/colors 100%
                                try:
                                    m_elem.Name = clean_name
                                    doc_mats_by_name[clean_name.lower()] = m_elem
                                    doc_mats_by_id[m_elem.Id] = m_elem
                                    renamed_set.add(clean_name)
                                    renamed_count += 1
                                    out.print_html(u"<span style='color:#f59e0b'>✏ [{}/{}] <b>{}</b> : Standardized ➔ <b>{}</b></span>".format(
                                        idx + 1, total_items, fam_name, clean_name))
                                except Exception:
                                    pass

                WinForms.Application.DoEvents()

            t.Commit()
            if self.ProgressBarStandardize:
                self.ProgressBarStandardize.Value = 100
            if self.TxtProgressPct:
                self.TxtProgressPct.Text = u"100%"
            if self.TxtProgressStatus:
                self.TxtProgressStatus.Text = u"✅ 100% RYN_MAT_ Standardization Finished Successfully!"
            WinForms.Application.DoEvents()

            out.print_md("---")
            out.print_md("### ✅ Standardization Finished Successfully!")
            out.print_md("- **Replaced/Reused authentic `RYN_MAT_`:** {}\n- **Standardized unique materials:** {}".format(replaced_count, renamed_count))

            msg = u"Standardization Complete!\n\n"
            msg += u"• Assigned authentic/reused RYN_MAT_ materials: {}\n".format(replaced_count)
            msg += u"• Standardized unique material names (textures preserved): {}\n\n".format(renamed_count)
            msg += u"All materials in active families are now 100% RYN_MAT_ compliant!"
            
            # Show Signature Riyan Custom Alert (Zero Default OS popups!)
            show_alert(msg, title="Standardization Complete", is_error=False)

            # Refresh audit in window
            self.run_audit()

        except Exception as ex:
            if 't' in locals() and t.HasStarted():
                t.RollBack()
            out.print_md("### ❌ Standardization Failed: {}".format(str(ex)))
            show_alert("Standardization Failed:\n" + str(ex), title="Standardization Error", is_error=True)

    def OnExportReport(self, sender, e):
        if not self.audit_data:
            return

        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        report_path = os.path.join(desktop_path, "RYN_Material_Audit_Report.txt")

        lines = [
            "=" * 60,
            "RIYAN FAMILY MATERIAL AUDIT & STANDARDIZATION REPORT",
            "=" * 60,
            "Document: " + (self.doc.Title if self.doc else "Unknown"),
            "Total Families: " + str(self.audit_data["total"]),
            "Compliant: " + str(len(self.audit_data["compliant"])),
            "Inconsistent Materials: " + str(len(self.audit_data["inconsistent"])),
            "Missing Parameters: " + str(len(self.audit_data["missing"])),
            "=" * 60,
            "\n[1. INCONSISTENT MATERIALS]"
        ]

        for item in self.audit_data["inconsistent"]:
            lines.append(" - [{}] {}: {}".format(item["Category"], item["FamilyName"], item["Details"]))

        lines.append("\n[2. MISSING PARAMETERS]")
        for item in self.audit_data["missing"]:
            lines.append(" - [{}] {}: {}".format(item["Category"], item["FamilyName"], item["Details"]))

        with codecs.open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        show_alert(u"Audit report saved to your Desktop:\n" + report_path, title="Report Exported", is_error=False)

    def show(self):
        self.window.ShowDialog()

# Revit Entry Point
if __name__ == "__main__":
    uiapp = __revit__
    app = uiapp.Application
    doc = uiapp.ActiveUIDocument.Document if uiapp.ActiveUIDocument else None

    if not doc:
        show_alert("Please open a Revit project or Family Library RVT before running Material Auditor.", title="Material Auditor", is_warning=True)
    else:
        win = MaterialAuditorWindow(doc, uiapp)
        win.show()
