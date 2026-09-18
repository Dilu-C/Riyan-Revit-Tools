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
clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")

import System
from System.Windows import Window, Application, WindowStartupLocation, WindowStyle
from System.Windows.Media import SolidColorBrush, Color, ColorConverter
from System.Windows.Interop import WindowInteropHelper
import Autodesk.Revit.DB as DB
from Autodesk.Revit.UI import TaskDialog

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

class MaterialAuditorWindow(Window):
    def __init__(self, doc, uiapp):
        self.doc = doc
        self.uiapp = uiapp
        self.is_dark_theme = True
        self.audit_data = None
        self.current_tab = "Inconsistent"

        xaml_path = os.path.join(os.path.dirname(__file__), "ui.xaml")
        with open(xaml_path, "r") as f:
            xaml_content = f.read()

        import System.IO as SIO
        from System.Windows.Markup import XamlReader
        str_reader = SIO.StringReader(xaml_content)
        xml_reader = System.Xml.XmlReader.Create(str_reader)
        self.window = XamlReader.Load(xml_reader)

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

            sym = self.doc.GetElement(symbols[0])
            param_names = [p.Definition.Name for p in sym.Parameters]

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
                        mapped_to = STANDARD_MATERIAL_MAP.get(m_name.lower(), "Needs Review")
                        mat_info.append(u"{}: '{}' -> {}".format(p_name, m_name, mapped_to))

            if has_inconsistent:
                inconsistent.append({
                    "FamilyName": fam_name,
                    "Category": cat_name,
                    "Details": u" | ".join(mat_info),
                    "BadgeText": u"Needs RYN_MAT",
                    "BadgeBg": SolidColorBrush(Color.FromRgb(80, 60, 10)),
                    "BadgeFg": SolidColorBrush(Color.FromRgb(245, 158, 11))
                })
            elif not missing:
                compliant.append({
                    "FamilyName": fam_name,
                    "Category": cat_name,
                    "Details": u"Fully standardized to RYN_MAT",
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

    def update_list_view(self):
        if not self.audit_data:
            return

        if self.current_tab == "Inconsistent":
            self.ItemsList.ItemsSource = self.audit_data["inconsistent"]
        elif self.current_tab == "Missing":
            self.ItemsList.ItemsSource = self.audit_data["missing"]
        else:
            self.ItemsList.ItemsSource = self.audit_data["compliant"]

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

    def OnTitleBarMouseDown(self, sender, e):
        try:
            from System.Windows.Input import MouseButton
            if e.ChangedButton == MouseButton.Left:
                self.window.DragMove()
        except Exception:
            pass

    def OnCloseClicked(self, sender, e):
        self.window.Close()

    def OnToggleTheme(self, sender, e):
        self.is_dark_theme = not self.is_dark_theme
        self.apply_theme()

    def OnApplyStandardization(self, sender, e):
        if not self.doc:
            TaskDialog.Show("Error", "No active document open to standardize.")
            return

        inconsistent_list = self.audit_data.get("inconsistent", []) if self.audit_data else []
        if not inconsistent_list:
            TaskDialog.Show("Material Auditor", "All families in this document are already RYN_MAT compliant!")
            return

        try:
            t = DB.Transaction(self.doc, "Apply RYN_MAT Standardization")
            t.Start()

            # Map all materials in doc
            mat_collector = DB.FilteredElementCollector(self.doc).OfClass(DB.Material)
            doc_materials = {m.Name.lower(): m.Id for m in mat_collector}

            updated_count = 0
            for item in inconsistent_list:
                fam_name = item["FamilyName"]
                collector = DB.FilteredElementCollector(self.doc).OfClass(DB.Family)
                for f in collector:
                    if f.Name == fam_name:
                        for sym_id in f.GetFamilySymbolIds():
                            sym = self.doc.GetElement(sym_id)
                            for p in sym.Parameters:
                                p_name = p.Definition.Name
                                if "Material" in p_name or "MAT" in p_name:
                                    m_id = p.AsElementId()
                                    if m_id and m_id != DB.ElementId.InvalidElementId:
                                        m_elem = self.doc.GetElement(m_id)
                                        if m_elem:
                                            curr_name_lower = m_elem.Name.lower()
                                            if curr_name_lower in STANDARD_MATERIAL_MAP:
                                                std_name = STANDARD_MATERIAL_MAP[curr_name_lower]
                                                if std_name.lower() in doc_materials:
                                                    p.Set(doc_materials[std_name.lower()])
                                                    updated_count += 1
                        break

            t.Commit()
            TaskDialog.Show("Standardization Complete", 
                            u"Successfully updated {} material parameter assignments to RYN_MAT standards!".format(updated_count))
            # Refresh audit
            self.run_audit()

        except Exception as ex:
            TaskDialog.Show("Standardization Failed", str(ex))

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

        TaskDialog.Show("Report Exported", u"Audit report saved to your Desktop:\n" + report_path)

    def show(self):
        self.window.ShowDialog()

# Revit Entry Point
if __name__ == "__main__":
    uiapp = __revit__
    app = uiapp.Application
    doc = uiapp.ActiveUIDocument.Document if uiapp.ActiveUIDocument else None

    if not doc:
        TaskDialog.Show("Material Auditor", "Please open a Revit project or Family Library RVT before running Material Auditor.")
    else:
        win = MaterialAuditorWindow(doc, uiapp)
        win.show()
