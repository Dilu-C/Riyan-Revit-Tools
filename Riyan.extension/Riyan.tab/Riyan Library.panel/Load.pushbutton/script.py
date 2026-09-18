# -*- coding: utf-8 -*-
"""
Riyan Family Library Browser (Load.pushbutton)
Seamless visual family content browser for Riyan BIM Standards.
Compatible with Autodesk Revit 2021 through Revit 2027+.
"""

import os
import sys
import json
import subprocess
import clr

clr.AddReference("System")
clr.AddReference("System.Drawing")
clr.AddReference("System.Windows.Forms")
clr.AddReference("PresentationFramework")
clr.AddReference("PresentationCore")
clr.AddReference("WindowsBase")

import System
from System.IO import Path, File
from System.Collections.Generic import List
from System.Windows import Window, WindowStartupLocation, Application, Visibility, Thickness
from System.Windows.Controls import ListBoxItem, Border, TextBlock, StackPanel, Image as WpfImage
from System.Windows.Media import Brushes, Color, SolidColorBrush
from System.Windows.Media.Imaging import BitmapImage, BitmapCacheOption
from System.Windows.Interop import WindowInteropHelper

# Revit API References
try:
    clr.AddReference('RevitAPI')
    clr.AddReference('RevitAPIUI')
    import Autodesk.Revit.DB as DB
    import Autodesk.Revit.UI as UI
    from pyrevit import revit, forms
    DOC = revit.doc
    UIDOC = revit.uidoc
    APP = revit.app
except Exception:
    DOC = None
    UIDOC = None
    APP = None

# -------------------------------------------------------------
# Configuration & Repository Locations
# -------------------------------------------------------------
SHAREPOINT_LIB_ROOT = os.path.expandvars(
    r"%USERPROFILE%\OneDrive - Riyan Private Limited\Riyan LK Projects - 00 - RIYAN REVIT STANDARD\02 LIBRARY"
)
CENTRAL_REPOSITORY = os.path.join(SHAREPOINT_LIB_ROOT, "00 RIYAN FAMILY REPOSITORY")
LOCAL_CACHE_DIR = os.path.expandvars(
    r"%APPDATA%\pyRevit\Extensions\Riyan-Revit-Tools\Library_Cache"
)
REVIT_2025_EXE = r"C:\Program Files\Autodesk\Revit 2025\Revit.exe"

# -------------------------------------------------------------
# Revit Family Load Options Handler
# -------------------------------------------------------------
class FamilyLoadHandler(DB.IFamilyLoadOptions):
    def OnFamilyFound(self, familyInUse, overwriteParameterValues):
        # Always overwrite parameter values cleanly to ensure updates take effect
        overwriteParameterValues.Value = True
        return True

    def OnSharedFamilyFound(self, sharedFamily, familyInUse, source, overwriteParameterValues):
        overwriteParameterValues.Value = True
        return True

# -------------------------------------------------------------
# Smart Name & Capability Parser
# -------------------------------------------------------------
def parse_family_metadata(rfa_path, category=None):
    filename = os.path.splitext(os.path.basename(rfa_path))[0]
    name_upper = filename.upper()
    
    # 1. Determine Discipline & Category
    disc = "ARCHITECTURAL"
    cat = category or "General"
    
    if "STR_" in name_upper or "STRUCTURAL" in name_upper or "REBAR" in name_upper or "BEAM" in name_upper:
        disc = "STRUCTURAL"
        cat = "Structural Framing"
    elif "PLUMBING" in name_upper or "PIPE" in name_upper or "BASIN" in name_upper or "WC" in name_upper or "TOILET" in name_upper:
        disc = "PLUMBING"
        cat = "Plumbing Fixtures"
    elif "FIRE" in name_upper or "SPRINKLER" in name_upper:
        disc = "FIRE PROTECTION"
        cat = "Fire Protection"
    elif "ACMV" in name_upper or "DUCT" in name_upper or "DIFFUSER" in name_upper or "FAN" in name_upper:
        disc = "ACMV"
        cat = "Mechanical Equipment"
    elif "ELEC" in name_upper or "LIGHT" in name_upper:
        disc = "ELECTRICAL"
        cat = "Electrical Fixtures"
    elif "WIN" in name_upper or "WINDOW" in name_upper:
        cat = "Windows"
    elif "DOR" in name_upper or "DOOR" in name_upper:
        cat = "Doors"
    elif "COL" in name_upper or "COLUMN" in name_upper:
        cat = "Columns"
    elif "TITLEBLOCK" in name_upper or "COVERPAGE" in name_upper or "TITLE" in name_upper:
        cat = "Title Blocks"
    elif "ANO_" in name_upper or "TAG" in name_upper:
        cat = "Annotations"

    # 2. Friendly Display Name
    display_title = filename
    for pfx in ["RYN_WIN_", "RYN_DOR_", "RYN_COL_", "RYN_ANO_", "RYN_STR_", "RYN_TitleBlock_", "RYN_CoverPage_"]:
        if display_title.startswith(pfx):
            display_title = display_title[len(pfx):]
            break
    display_title = display_title.replace("_", " ").replace(".", " ").strip()
    if cat == "Windows" and not "Window" in display_title:
        display_title += " Window"
    elif cat == "Doors" and not "Door" in display_title:
        display_title += " Door"

    # 3. Detect Capability Badges
    badges = []
    if "TOPHUNG" in name_upper or "TOP HUNG" in name_upper:
        badges.append({"label": "Top Hung", "icon": "🪟", "bg": "#0369A1"})
    if "SWING" in name_upper or "SIDE HUNG" in name_upper:
        badges.append({"label": "Swing / Side Hung", "icon": "🪟", "bg": "#0284C7"})
    if "SLIDING" in name_upper:
        badges.append({"label": "Sliding", "icon": "↔", "bg": "#2563EB"})
    if "POCKET" in name_upper:
        badges.append({"label": "Pocket Door", "icon": "🚪", "bg": "#4F46E5"})
    if "LOUVER" in name_upper:
        badges.append({"label": "Louver Panels", "icon": "🪜", "bg": "#D97706"})
    if "MULTYPANEL" in name_upper or "MULTI" in name_upper or "4 PANEL" in name_upper:
        badges.append({"label": "Multi-Panel", "icon": "🔲", "bg": "#0D9488"})
    if "FOLDING" in name_upper:
        badges.append({"label": "Folding", "icon": "⚡", "bg": "#7C3AED"})
    if "PIVOT" in name_upper:
        badges.append({"label": "Pivot Action", "icon": "🔄", "bg": "#9333EA"})
    
    # Always include Parametric & Material badges
    badges.append({"label": "Parametric", "icon": "📏", "bg": "#15803D"})
    badges.append({"label": "Material Finishes", "icon": "🎨", "bg": "#475569"})

    return {
        "title": display_title,
        "code": filename,
        "discipline": disc,
        "category": cat,
        "rfa_path": rfa_path,
        "badges": badges,
        "types": ["Standard / Default Type"]
    }

# -------------------------------------------------------------
# Main Browser Window
# -------------------------------------------------------------
class RiyanFamilyBrowser(forms.WPFWindow):
    def __init__(self, xaml_file_path):
        forms.WPFWindow.__init__(self, xaml_file_path)
        self.catalog = []
        self.filtered_families = []
        self.selected_family = None
        self.current_discipline = "ALL"
        self.current_category = "ALL"

        # Win32 HWND Ownership
        if UIDOC and hasattr(UIDOC, "Application"):
            try:
                handle = UIDOC.Application.MainWindowHandle
                WindowInteropHelper(self).Owner = handle
            except Exception:
                pass

        # Event Handlers
        self.BtnClose.Click += self.on_close
        self.BtnFooterClose.Click += self.on_close
        self.BtnAdminSync.Click += self.on_admin_sync
        self.TitleBar.MouseLeftButtonDown += self.on_drag_move
        self.TxtSearch.TextChanged += self.on_search_changed
        self.LstCategories.SelectionChanged += self.on_category_changed
        self.LstFamilies.SelectionChanged += self.on_family_selected
        
        self.BtnLoadFamily.Click += self.on_load_family
        self.BtnLoadTypeOnly.Click += self.on_load_type_only
        self.BtnFooterLoad.Click += self.on_load_family
        self.BtnEdit2025.Click += self.on_edit_2025

        # Admin Protection Guardrail: Hide Edit and Sync buttons for standard users
        try:
            uname = System.Environment.UserName.lower()
            ADMIN_USERS = ["user", "dilupa", "dilupa.chathuranga", "dilupac", "dilupa1990"]
            self.is_admin = uname in ADMIN_USERS
            if not self.is_admin:
                self.BtnEdit2025.Visibility = Visibility.Collapsed
                self.BtnAdminSync.Visibility = Visibility.Collapsed
        except Exception:
            pass

        # Discipline Tabs
        self.TabAll.Checked += lambda s, e: self.set_discipline("ALL")
        self.TabArc.Checked += lambda s, e: self.set_discipline("ARCHITECTURAL")
        self.TabStr.Checked += lambda s, e: self.set_discipline("STRUCTURAL")
        self.TabPlumb.Checked += lambda s, e: self.set_discipline("PLUMBING")
        self.TabElec.Checked += lambda s, e: self.set_discipline("ELECTRICAL")
        self.TabFire.Checked += lambda s, e: self.set_discipline("FIRE PROTECTION")
        self.TabAcmv.Checked += lambda s, e: self.set_discipline("ACMV")

        # Load Catalog Data
        self.load_catalog_data()

    def on_drag_move(self, sender, e):
        try:
            self.DragMove()
        except:
            pass

    def on_close(self, sender, e):
        self.Close()

    def load_catalog_data(self):
        catalog_path = os.path.join(CENTRAL_REPOSITORY, "catalog.json")
        fallback_path = os.path.join(LOCAL_CACHE_DIR, "catalog.json")

        self.catalog = []
        target_path = None
        if os.path.exists(catalog_path):
            target_path = catalog_path
            self.TxtStatus.Text = u"SharePoint Library Connected (BIM SERVER)"
        elif os.path.exists(fallback_path):
            target_path = fallback_path
            self.TxtStatus.Text = u"Local Cached Library (Offline Mode)"
        else:
            # Fallback: scan known local folders
            self.TxtStatus.Text = u"Scanning local Riyan Standard folders..."
            self.build_live_catalog_from_folders()
            return

        if target_path:
            try:
                with open(target_path, 'r') as f:
                    self.catalog = json.load(f)
            except Exception as ex:
                self.build_live_catalog_from_folders()

        self.refresh_categories()
        self.apply_filter()

    def build_live_catalog_from_folders(self):
        """Scans SharePoint / Local Riyan repositories for RFA files on-the-fly."""
        folders_to_scan = [
            SHAREPOINT_LIB_ROOT,
            r"C:\Users\User\Desktop\RIYAN\00 - RIYAN STANDARD",
            r"C:\Users\User\Desktop\RIYAN\Other\Family"
        ]
        items = []
        seen = set()
        for root_dir in folders_to_scan:
            if not os.path.exists(root_dir):
                continue
            for root, dirs, files in os.walk(root_dir):
                cat_name = os.path.basename(root)
                for f in files:
                    if f.lower().endswith(".rfa"):
                        p = os.path.join(root, f)
                        fn_clean = os.path.splitext(f)[0]
                        if fn_clean in seen:
                            continue
                        seen.add(fn_clean)
                        meta = parse_family_metadata(p, cat_name)
                        # Check thumbnail
                        thumb_path = p.replace(".rfa", ".png")
                        if os.path.exists(thumb_path):
                            meta["thumbnail"] = thumb_path
                        items.append(meta)

        self.catalog = items
        self.TxtStatus.Text = u"Live Scanned {} Riyan Families".format(len(items))
        self.refresh_categories()
        self.apply_filter()

    def set_discipline(self, disc):
        self.current_discipline = disc
        self.refresh_categories()
        self.apply_filter()

    def refresh_categories(self):
        self.LstCategories.Items.Clear()
        
        # Count per category in active discipline
        counts = {}
        for item in self.catalog:
            if self.current_discipline != "ALL" and item.get("discipline") != self.current_discipline:
                continue
            c = item.get("category", "General")
            counts[c] = counts.get(c, 0) + 1

        total = sum(counts.values())
        
        # Add 'All' item
        all_item = ListBoxItem()
        all_item.Content = u"All Categories ({})".format(total)
        all_item.Tag = "ALL"
        self.LstCategories.Items.Add(all_item)
        all_item.IsSelected = True

        # Add categories sorted
        for cat in sorted(counts.keys()):
            lbi = ListBoxItem()
            lbi.Content = u"{} ({})".format(cat, counts[cat])
            lbi.Tag = cat
            self.LstCategories.Items.Add(lbi)

    def on_category_changed(self, sender, e):
        sel = self.LstCategories.SelectedItem
        if sel and hasattr(sel, "Tag"):
            self.current_category = sel.Tag
        else:
            self.current_category = "ALL"
        self.apply_filter()

    def on_search_changed(self, sender, e):
        txt = self.TxtSearch.Text.strip()
        self.TxtSearchPlaceholder.Visibility = Visibility.Collapsed if txt else Visibility.Visible
        self.apply_filter()

    def apply_filter(self):
        query = self.TxtSearch.Text.strip().lower()
        self.filtered_families = []
        self.LstFamilies.Items.Clear()

        for item in self.catalog:
            if self.current_discipline != "ALL" and item.get("discipline") != self.current_discipline:
                continue
            if self.current_category != "ALL" and item.get("category") != self.current_category:
                continue
            
            # Search query matching
            if query:
                title = item.get("title", "").lower()
                code = item.get("code", "").lower()
                cat = item.get("category", "").lower()
                types_str = " ".join(item.get("types", [])).lower()
                if query not in title and query not in code and query not in cat and query not in types_str:
                    continue

            self.filtered_families.append(item)

        self.TxtResultsCount.Text = u"{} Families Found".format(len(self.filtered_families))

        # Populate Cards
        for fam in self.filtered_families:
            card = self.create_family_card(fam)
            self.LstFamilies.Items.Add(card)

    def create_family_card(self, fam):
        lbi = ListBoxItem()
        lbi.Tag = fam

        sp = StackPanel()
        sp.Margin = Thickness(8)

        # Thumbnail Image Container
        img_border = Border()
        img_border.Height = 115
        img_border.CornerRadius = System.Windows.CornerRadius(6)
        img_border.Background = SolidColorBrush(Color.FromRgb(24, 24, 27))
        img_border.Margin = Thickness(0, 0, 0, 8)
        img_border.ClipToBounds = True

        img = WpfImage()
        img.Stretch = System.Windows.Media.Stretch.Uniform
        thumb_path = fam.get("thumbnail")
        if thumb_path and os.path.exists(thumb_path):
            try:
                bi = BitmapImage()
                bi.BeginInit()
                bi.CacheOption = BitmapCacheOption.OnLoad
                bi.UriSource = System.Uri(thumb_path)
                bi.EndInit()
                img.Source = bi
            except:
                pass
        img_border.Child = img
        sp.Children.Add(img_border)

        # Title
        txt_title = TextBlock()
        txt_title.Text = fam.get("title", fam.get("code", "Family"))
        txt_title.FontSize = 11
        txt_title.FontWeight = System.Windows.FontWeights.Bold
        txt_title.Foreground = SolidColorBrush(Color.FromRgb(244, 244, 245))
        txt_title.TextTrimming = System.Windows.TextTrimming.CharacterEllipsis
        txt_title.MaxHeight = 32
        txt_title.TextWrapping = System.Windows.TextWrapping.Wrap
        sp.Children.Add(txt_title)

        # Category & Chips
        txt_cat = TextBlock()
        txt_cat.Text = fam.get("category", "")
        txt_cat.FontSize = 10
        txt_cat.Foreground = SolidColorBrush(Color.FromRgb(113, 113, 122))
        txt_cat.Margin = Thickness(0, 2, 0, 0)
        sp.Children.Add(txt_cat)

        lbi.Content = sp
        return lbi

    def on_family_selected(self, sender, e):
        sel = self.LstFamilies.SelectedItem
        if not sel or not hasattr(sel, "Tag") or not sel.Tag:
            self.PanelDetail.Visibility = Visibility.Collapsed
            self.selected_family = None
            return

        fam = sel.Tag
        self.selected_family = fam
        self.PanelDetail.Visibility = Visibility.Visible

        # Update Detail Inspector
        self.TxtDetailTitle.Text = fam.get("title", "")
        self.TxtDetailCode.Text = fam.get("code", "")
        self.TxtDetailDiscipline.Text = fam.get("discipline", "ARCHITECTURAL")
        self.TxtDetailCategory.Text = fam.get("category", "General")

        # Preview Image
        thumb_path = fam.get("thumbnail")
        if thumb_path and os.path.exists(thumb_path):
            try:
                bi = BitmapImage()
                bi.BeginInit()
                bi.CacheOption = BitmapCacheOption.OnLoad
                bi.UriSource = System.Uri(thumb_path)
                bi.EndInit()
                self.ImgDetailPreview.Source = bi
            except:
                self.ImgDetailPreview.Source = None
        else:
            self.ImgDetailPreview.Source = None

        # Render Graphic Option Badges
        self.PanelBadges.Children.Clear()
        for b in fam.get("badges", []):
            badge_border = Border()
            badge_border.CornerRadius = System.Windows.CornerRadius(4)
            badge_border.Background = SolidColorBrush(Color.FromRgb(39, 39, 42))
            badge_border.Padding = Thickness(8, 4, 8, 4)
            badge_border.Margin = Thickness(0, 0, 6, 6)

            badge_sp = StackPanel()
            badge_sp.Orientation = System.Windows.Controls.Orientation.Horizontal

            ico = TextBlock()
            ico.Text = b.get("icon", "✔") + " "
            ico.FontSize = 10
            ico.Foreground = SolidColorBrush(Color.FromRgb(56, 189, 248))
            badge_sp.Children.Add(ico)

            lbl = TextBlock()
            lbl.Text = b.get("label", "")
            lbl.FontSize = 10
            lbl.FontWeight = System.Windows.FontWeights.SemiBold
            lbl.Foreground = SolidColorBrush(Color.FromRgb(228, 228, 231))
            badge_sp.Children.Add(lbl)

            badge_border.Child = badge_sp
            self.PanelBadges.Children.Add(badge_border)

        # Render Types Dropdown
        self.CmbTypes.Items.Clear()
        types = fam.get("types", ["Standard Type"])
        for t in types:
            self.CmbTypes.Items.Add(t)
        if self.CmbTypes.Items.Count > 0:
            self.CmbTypes.SelectedIndex = 0

        # Render Parameters Table
        self.PanelParams.Children.Clear()
        specs = fam.get("specs", {
            "Operation": "Parametric Visibility / Smart Controls",
            "Dimensions": "Width & Height Parametric",
            "Materials": "Configurable (Aluminium, Timber, Glass)"
        })
        for k, v in specs.items():
            row = StackPanel()
            row.Orientation = System.Windows.Controls.Orientation.Horizontal
            row.Margin = Thickness(0, 2, 0, 2)

            t_k = TextBlock()
            t_k.Text = k + ": "
            t_k.Width = 90
            t_k.FontSize = 11
            t_k.Foreground = SolidColorBrush(Color.FromRgb(113, 113, 122))
            row.Children.Add(t_k)

            t_v = TextBlock()
            t_v.Text = str(v)
            t_v.FontSize = 11
            t_v.FontWeight = System.Windows.FontWeights.SemiBold
            t_v.Foreground = SolidColorBrush(Color.FromRgb(244, 244, 245))
            row.Children.Add(t_v)

            self.PanelParams.Children.Add(row)

    def on_load_family(self, sender, e):
        if not self.selected_family:
            forms.alert(u"Please select a family from the list to load.", title=u"Load Family")
            return
        
        rfa_path = self.selected_family.get("rfa_path")
        if not rfa_path or not os.path.exists(rfa_path):
            forms.alert(u"Family file could not be found at path:\n{}".format(rfa_path), title=u"File Missing")
            return

        if not DOC:
            forms.alert(u"No active Revit document found.", title=u"Revit Document")
            return

        self.Topmost = True
        try:
            t = DB.Transaction(DOC, "Load Riyan Family: " + self.selected_family.get("title", ""))
            t.Start()
            handler = FamilyLoadHandler()
            loaded_family = clr.Reference[DB.Family]()
            success = DOC.LoadFamily(rfa_path, handler, loaded_family)
            t.Commit()

            fam_name = self.selected_family.get('title')
            self.TxtStatus.Text = u"Successfully Loaded: {}".format(fam_name)
            forms.alert(u"Family '{}' was successfully loaded into the active project!".format(fam_name), 
                        title=u"Family Loaded 👍")
        except Exception as ex:
            forms.alert(u"Failed to load family:\n{}".format(str(ex)), title=u"Load Error")
        finally:
            self.Topmost = False

    def on_load_type_only(self, sender, e):
        # Loads family and activates the specific type chosen in the dropdown
        if not self.selected_family:
            return
        sel_type = self.CmbTypes.SelectedItem
        self.on_load_family(sender, e)

    def on_edit_2025(self, sender, e):
        if not self.selected_family:
            return
        rfa_path = self.selected_family.get("rfa_path")
        if not rfa_path or not os.path.exists(rfa_path):
            forms.alert(u"Family file path does not exist.", title=u"Error")
            return

        if not os.path.exists(REVIT_2025_EXE):
            forms.alert(u"Autodesk Revit 2025 was not found at default location:\n{}\nPlease open manually in Revit 2025.".format(REVIT_2025_EXE), title=u"Revit 2025 Not Found")
            return

        try:
            subprocess.Popen([REVIT_2025_EXE, rfa_path])
            forms.alert(u"Launching family directly in Autodesk Revit 2025:\n\n{}\n\nThis ensures company-wide backward compatibility across Revit 2025, 2026, and 2027!".format(os.path.basename(rfa_path)), title=u"Opening in Revit 2025 🛠")
        except Exception as ex:
            forms.alert(u"Could not launch Revit 2025:\n{}".format(str(ex)), title=u"Launch Error")

    def on_admin_sync(self, sender, e):
        """Admin sync / extract utility."""
        res = forms.CommandSwitchWindow.show(
            ["1. ⚡ Quick Sync (Scan RFA Files & Extract Thumbnails)",
             "2. 📦 Extract All Families from Active Document",
             "3. 📂 Open SharePoint Library Folder"],
            message="Riyan Library Admin & Sync Utilities"
        )
        if not res:
            return

        if res.startswith("1."):
            self.run_quick_sync()
        elif res.startswith("2."):
            self.extract_from_active_doc()
        elif res.startswith("3."):
            try:
                subprocess.Popen(["explorer.exe", SHAREPOINT_LIB_ROOT])
            except:
                pass

    def run_quick_sync(self):
        # Trigger PowerShell catalog compiler
        self.TxtStatus.Text = u"Compiling Catalog & Extracting Thumbnails..."
        self.build_live_catalog_from_folders()
        forms.alert(u"Quick Sync Complete! {} families indexed.".format(len(self.catalog)), title=u"Sync Done")

    def extract_from_active_doc(self):
        if not DOC:
            forms.alert(u"No active document open.", title=u"Extract Error")
            return
        doc_title = DOC.Title
        if not forms.alert(u"Extract all loadable families from '{}'?\nThis will save .rfa files into the SharePoint library repository.".format(doc_title), yes=True, no=True):
            return

        out_dir = os.path.join(CENTRAL_REPOSITORY, "Families", "Architectural")
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        count = 0
        collector = DB.FilteredElementCollector(DOC).OfClass(DB.Family)
        for fam in collector:
            if not fam.IsInPlace and fam.IsEditable:
                try:
                    f_name = fam.Name
                    target_rfa = os.path.join(out_dir, f_name + ".rfa")
                    fam_doc = DOC.EditFamily(fam)
                    opt = DB.SaveAsOptions()
                    opt.OverwriteExistingFile = True
                    fam_doc.SaveAs(target_rfa, opt)
                    fam_doc.Close(False)
                    count += 1
                except Exception:
                    pass

        forms.alert(u"Extraction Finished!\n{} families saved to SharePoint Library.".format(count), title=u"Extraction Done")
        self.build_live_catalog_from_folders()

# -------------------------------------------------------------
# Entry Point
# -------------------------------------------------------------
if __name__ == "__main__":
    xaml_file = os.path.join(os.path.dirname(__file__), "ui.xaml")
    win = RiyanFamilyBrowser(xaml_file)
    win.ShowDialog()
