# -*- coding: utf-8 -*-
"""
Riyan Family Library Browser (Load.pushbutton)
Seamless visual family content browser for Riyan BIM Standards.
Compatible with Autodesk Revit 2021 through Revit 2027+.
"""

import os
import sys
import json
import codecs
import subprocess
import clr

clr.AddReference("System")
clr.AddReference("System.IO")
clr.AddReference("System.Drawing")
clr.AddReference("System.Windows.Forms")
clr.AddReference("PresentationFramework")
clr.AddReference("PresentationCore")
clr.AddReference("WindowsBase")

import System
from System.IO import Path, File, MemoryStream
from System.Collections.Generic import List
from System.Windows import Window, WindowStartupLocation, Application, Visibility, Thickness
from System.Windows.Controls import ListBoxItem, Border, TextBlock, StackPanel, Image as WpfImage
from System.Windows.Media import Brushes, Color, SolidColorBrush
from System.Windows.Media.Imaging import BitmapImage, BitmapCacheOption, BitmapCreateOptions
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
THUMBNAILS_DIR = os.path.join(CENTRAL_REPOSITORY, "Thumbnails")
LOCAL_CACHE_DIR = os.path.expandvars(
    r"%APPDATA%\pyRevit\Extensions\Riyan-Revit-Tools\Library_Cache"
)
REVIT_2025_EXE = r"C:\Program Files\Autodesk\Revit 2025\Revit.exe"

# -------------------------------------------------------------
# Revit Family Load Options Handler
# -------------------------------------------------------------
class FamilyLoadHandler(DB.IFamilyLoadOptions):
    def OnFamilyFound(self, familyInUse, overwriteParameterValues):
        overwriteParameterValues.Value = True
        return True

    def OnSharedFamilyFound(self, sharedFamily, familyInUse, source, overwriteParameterValues):
        overwriteParameterValues.Value = True
        return True

def is_valid_3d_thumbnail(image_path):
    if not image_path:
        return False
    try:
        if not os.path.exists(image_path):
            return False
        # Strict Generic Revit Blue RFA Icon Rejection (8717 bytes or < 500 bytes)
        size = os.path.getsize(image_path)
        if size == 8717 or size < 500:
            return False
        return True
    except Exception:
        return False

def load_bitmap(image_path):
    if not is_valid_3d_thumbnail(image_path):
        return None
    try:
        bi = BitmapImage()
        bi.BeginInit()
        bi.CacheOption = BitmapCacheOption.OnLoad
        bi.UriSource = System.Uri(image_path, System.UriKind.Absolute)
        bi.EndInit()
        bi.Freeze()
        return bi
    except Exception:
        try:
            bytes_data = File.ReadAllBytes(image_path)
            ms = MemoryStream(bytes_data)
            bi = BitmapImage()
            bi.BeginInit()
            bi.CacheOption = BitmapCacheOption.OnLoad
            bi.StreamSource = ms
            bi.EndInit()
            bi.Freeze()
            return bi
        except Exception:
            return None

# -------------------------------------------------------------
# Smart Level-Based Categorizer
# -------------------------------------------------------------
def categorize_by_level_rule(filename, directory_name=""):
    name_upper = filename.upper()
    dir_upper = directory_name.upper()

    disc = "ARCHITECTURAL"
    if "STR_" in name_upper or "STRUCTURAL" in dir_upper or "REBAR" in name_upper or "BEAM" in name_upper:
        disc = "STRUCTURAL"
    elif "PLUMBING" in name_upper or "PLUMBING" in dir_upper or "BASIN" in name_upper or "TOILET" in name_upper or "WC" in name_upper:
        disc = "PLUMBING"
    elif "FIRE" in name_upper or "SPRINKLER" in name_upper or "FIRE" in dir_upper:
        disc = "FIRE PROTECTION"
    elif "ACMV" in name_upper or "DUCT" in name_upper or "DIFFUSER" in name_upper or "ACMV" in dir_upper:
        disc = "ACMV"
    elif "ELEC" in name_upper or "LIGHT" in name_upper or "ELECTRICAL" in dir_upper:
        disc = "ELECTRICAL"

    # Category matching Dilupa's RVT Levels
    cat = "General"
    if disc == "ARCHITECTURAL":
        if "DOR" in name_upper or "DOOR" in dir_upper:
            if "SLIDING" in name_upper or "BARN" in name_upper or "POCKET" in name_upper:
                cat = "Door-Sliding"
            elif "SWING" in name_upper or "PIVOT" in name_upper or "DOUBLE" in name_upper:
                cat = "Door-Swing"
            else:
                cat = "Door-Other"
        elif "WIN" in name_upper or "WINDOW" in dir_upper:
            if "TOPHUNG" in name_upper or "TOP HUNG" in name_upper or "AWNING" in name_upper:
                cat = "Window-TopHung"
            elif "SLIDING" in name_upper:
                cat = "Window-Sliding"
            elif "FIXED" in name_upper or "FIX" in name_upper:
                cat = "Window-Fixed"
            else:
                cat = "Window-Other"
        elif "TITLEBLOCK" in name_upper or "COVERPAGE" in name_upper or "TITLE" in dir_upper:
            cat = "Annotation-TitleBlocks"
        elif "ANO_" in name_upper or "TAG" in name_upper or "ANNOTAT" in dir_upper:
            cat = "Annotation-Tags"
        elif "SOFA" in dir_upper or "CHAIR" in dir_upper or "TABLE" in dir_upper or "FURNITURE" in dir_upper:
            cat = "Furniture-General"
        elif "COL" in name_upper or "COLUMN" in dir_upper:
            cat = "Architecture-Columns"
        else:
            cat = "Arch-Other"
    elif disc == "STRUCTURAL":
        if "BEAM" in name_upper:
            cat = "Structure-Beams"
        elif "COL" in name_upper:
            cat = "Structure-Columns"
        elif "REBAR" in name_upper:
            cat = "Structure-Rebar"
        else:
            cat = "Structure-General"
    elif disc == "PLUMBING":
        cat = "Plumbing-Fixtures"
    elif disc == "FIRE PROTECTION":
        cat = "Fire-Protection"
    elif disc == "ACMV":
        cat = "ACMV-Equipment"
    elif disc == "ELECTRICAL":
        cat = "Electrical-Fixtures"

    return disc, cat

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
        self.is_dark_theme = True
        self.view_mode = "Medium"

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
        self.BtnToggleTheme.Click += self.on_toggle_theme
        self.TitleBar.MouseLeftButtonDown += self.on_drag_move
        self.TxtSearch.TextChanged += self.on_search_changed
        self.LstCategories.SelectionChanged += self.on_category_changed
        self.LstFamilies.SelectionChanged += self.on_family_selected

        # Mouse Wheel Anywhere Scrolling Support
        if hasattr(self, "CardsScrollViewer") and self.CardsScrollViewer:
            self.CardsScrollViewer.PreviewMouseWheel += self.on_cards_preview_mouse_wheel
        if hasattr(self, "LstFamilies") and self.LstFamilies:
            self.LstFamilies.PreviewMouseWheel += self.on_cards_preview_mouse_wheel

        # View Mode Segmented Buttons
        view_btns = [
            ("BtnViewXL", "ExtraLarge"),
            ("BtnViewL", "Large"),
            ("BtnViewM", "Medium"),
            ("BtnViewS", "Small"),
            ("BtnViewList", "List")
        ]
        for b_name, mode in view_btns:
            btn = getattr(self, b_name, None)
            if btn:
                def make_handler(m):
                    return lambda s, e: self.set_view_mode(m)
                btn.Checked += make_handler(mode)
        
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

    def on_toggle_theme(self, sender, e):
        self.is_dark_theme = not self.is_dark_theme
        self.apply_theme()

    def apply_theme(self):
        if self.is_dark_theme:
            self.BtnToggleTheme.Content = u"🌓 Dark"
            self.Resources["WindowBg"] = SolidColorBrush(Color.FromRgb(24, 24, 27))
            self.Resources["SurfaceBg"] = SolidColorBrush(Color.FromRgb(18, 18, 21))
            self.Resources["CardBg"] = SolidColorBrush(Color.FromRgb(32, 32, 36))
            self.Resources["BorderColor"] = SolidColorBrush(Color.FromRgb(46, 46, 51))
            self.Resources["TextPrimary"] = SolidColorBrush(Color.FromRgb(244, 244, 245))
            self.Resources["TextSecondary"] = SolidColorBrush(Color.FromRgb(161, 161, 170))
            self.Resources["TextMuted"] = SolidColorBrush(Color.FromRgb(113, 113, 122))
            self.Background = self.Resources["WindowBg"]
            self.Foreground = self.Resources["TextPrimary"]
        else:
            self.BtnToggleTheme.Content = u"☀️ Light"
            self.Resources["WindowBg"] = SolidColorBrush(Color.FromRgb(248, 250, 252)) # Slate 50
            self.Resources["SurfaceBg"] = SolidColorBrush(Color.FromRgb(255, 255, 255))
            self.Resources["CardBg"] = SolidColorBrush(Color.FromRgb(255, 255, 255))
            self.Resources["BorderColor"] = SolidColorBrush(Color.FromRgb(203, 213, 225)) # Slate 300
            self.Resources["TextPrimary"] = SolidColorBrush(Color.FromRgb(15, 23, 42))     # Deep Pitch Black/Slate
            self.Resources["TextSecondary"] = SolidColorBrush(Color.FromRgb(51, 65, 85))   # Dark Slate 700
            self.Resources["TextMuted"] = SolidColorBrush(Color.FromRgb(100, 116, 139))   # Slate 500
            self.Background = self.Resources["WindowBg"]
            self.Foreground = self.Resources["TextPrimary"]

        # Controls text contrast
        for rb in [self.TabAll, self.TabArc, self.TabStr, self.TabPlumb, self.TabElec, self.TabFire, self.TabAcmv]:
            if rb and not rb.IsChecked:
                rb.Foreground = self.Resources["TextSecondary"]

        # View Mode Segmented Buttons Contrast
        for b_name in ["BtnViewXL", "BtnViewL", "BtnViewM", "BtnViewS", "BtnViewList"]:
            b = getattr(self, b_name, None)
            if b:
                if b.IsChecked:
                    b.Foreground = SolidColorBrush(Color.FromRgb(255, 255, 255))
                else:
                    b.Foreground = self.Resources["TextSecondary"]

        # Update and re-render
        self.refresh_categories()
        self.apply_filter()

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

        if target_path:
            try:
                with codecs.open(target_path, 'r', 'utf-8-sig') as f:
                    raw_items = json.load(f)
                    import re
                    # Strict Zero-Backup & Mandatory 3D Thumbnail Guardrail
                    cache_thumbs = os.path.join(LOCAL_CACHE_DIR, "Thumbnails")
                    self.catalog = []
                    for item in raw_items:
                        c = item.get("code", "")
                        r = item.get("rfa_path", "")
                        if re.search(r'\.\d{3,4}$', c) or re.search(r'\.\d{3,4}\.rfa$', r, re.IGNORECASE):
                            continue
                        
                        t = item.get("thumbnail")
                        if not is_valid_3d_thumbnail(t):
                            c1 = os.path.join(THUMBNAILS_DIR, c + ".png")
                            c2 = os.path.join(cache_thumbs, c + ".png")
                            if is_valid_3d_thumbnail(c1):
                                item["thumbnail"] = c1
                            elif is_valid_3d_thumbnail(c2):
                                item["thumbnail"] = c2
                            else:
                                continue # Bypass unconditionally! Zero placeholder icons!
                        self.catalog.append(item)
            except Exception as ex:
                self.build_live_catalog_from_folders()
        else:
            self.build_live_catalog_from_folders()

        self.refresh_categories()
        self.apply_filter()

    def build_live_catalog_from_folders(self):
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
                for f in files:
                    if f.lower().endswith(".rfa"):
                        p = os.path.join(root, f)
                        fn_clean = os.path.splitext(f)[0]
                        if fn_clean in seen:
                            continue
                        seen.add(fn_clean)
                        
                        disc, cat = categorize_by_level_rule(fn_clean, os.path.basename(root))
                        
                        # Friendly Title
                        t_clean = fn_clean
                        for pfx in ["RYN_WIN_", "RYN_DOR_", "RYN_COL_", "RYN_ANO_", "RYN_STR_", "RYN_TitleBlock_", "RYN_CoverPage_"]:
                            if t_clean.startswith(pfx):
                                t_clean = t_clean[len(pfx):]
                                break
                        t_clean = t_clean.replace("_", " ").replace(".", " ").strip()
                        if cat.startswith("Window") and "Window" not in t_clean:
                            t_clean += " Window"
                        elif cat.startswith("Door") and "Door" not in t_clean:
                            t_clean += " Door"

                        # Option Badges
                        n_up = fn_clean.upper()
                        badges = []
                        if "TOPHUNG" in n_up or "TOP HUNG" in n_up:
                            badges.append({"label": "Top Hung", "icon": "🪟", "bg": "#0369A1"})
                        if "SWING" in n_up or "SIDE HUNG" in n_up:
                            badges.append({"label": "Swing / Side Hung", "icon": "🪟", "bg": "#0284C7"})
                        if "SLIDING" in n_up:
                            badges.append({"label": "Sliding", "icon": "↔", "bg": "#2563EB"})
                        if "POCKET" in n_up:
                            badges.append({"label": "Pocket Door", "icon": "🚪", "bg": "#4F46E5"})
                        if "LOUVER" in n_up:
                            badges.append({"label": "Louver Panels", "icon": "🪜", "bg": "#D97706"})
                        if "MULTYPANEL" in n_up or "MULTI" in n_up or "4 PANEL" in n_up:
                            badges.append({"label": "Multi-Panel", "icon": "🔲", "bg": "#0D9488"})
                        badges.append({"label": "Parametric", "icon": "📏", "bg": "#15803D"})
                        badges.append({"label": "Custom Materials", "icon": "🎨", "bg": "#475569"})

                        thumb_file = os.path.join(THUMBNAILS_DIR, fn_clean + ".png")
                        thumb_ref = thumb_file if os.path.exists(thumb_file) else ""

                        items.append({
                            "title": t_clean,
                            "code": fn_clean,
                            "discipline": disc,
                            "category": cat,
                            "rfa_path": p,
                            "thumbnail": thumb_ref,
                            "badges": badges,
                            "types": ["Standard Type"]
                        })

        self.catalog = items
        self.TxtStatus.Text = u"Live Scanned {} Level Families".format(len(items))
        self.refresh_categories()
        self.apply_filter()

    def set_discipline(self, disc):
        self.current_discipline = disc
        self.refresh_categories()
        self.apply_filter()

    def refresh_categories(self):
        self.LstCategories.Items.Clear()
        
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
        all_item.Foreground = self.Resources["TextPrimary"]
        self.LstCategories.Items.Add(all_item)
        all_item.IsSelected = True

        for cat in sorted(counts.keys()):
            lbi = ListBoxItem()
            lbi.Content = u"{} ({})".format(cat, counts[cat])
            lbi.Tag = cat
            lbi.Foreground = self.Resources["TextPrimary"]
            self.LstCategories.Items.Add(lbi)

    def on_category_changed(self, sender, e):
        sel = self.LstCategories.SelectedItem
        if sel and hasattr(sel, "Tag"):
            self.current_category = sel.Tag
        else:
            self.current_category = "ALL"
        self.apply_filter()

    def on_cards_preview_mouse_wheel(self, sender, e):
        """Allows smooth scrolling anywhere when cursor is over the family cards grid."""
        try:
            e.Handled = True
            scroll_delta = e.Delta
            current_offset = self.CardsScrollViewer.VerticalOffset
            new_offset = current_offset - (scroll_delta * 0.8)
            self.CardsScrollViewer.ScrollToVerticalOffset(new_offset)
        except Exception:
            pass

    def set_view_mode(self, mode):
        """Switches thumbnail view size: Extra Large, Large, Medium, Small, List."""
        self.view_mode = mode
        # Update foreground highlights
        for b_name in ["BtnViewXL", "BtnViewL", "BtnViewM", "BtnViewS", "BtnViewList"]:
            b = getattr(self, b_name, None)
            if b:
                if b.IsChecked:
                    b.Foreground = SolidColorBrush(Color.FromRgb(255, 255, 255))
                else:
                    b.Foreground = self.Resources["TextSecondary"]
        self.apply_filter()

    def on_search_changed(self, sender, e):
        txt = self.TxtSearch.Text.strip()
        self.TxtSearchPlaceholder.Visibility = Visibility.Collapsed if txt else Visibility.Visible
        self.apply_filter()

    def apply_filter(self):
        query = self.TxtSearch.Text.strip().lower()
        self.filtered_families = []
        self.LstFamilies.Items.Clear()
        import re

        for item in self.catalog:
            code = item.get("code", "")
            rfa = item.get("rfa_path", "")
            
            # 1. Zero-Backup Filter: Strictly bypass .0001, .0002 etc.
            if re.search(r'\.\d{3,4}$', code) or re.search(r'\.\d{3,4}\.rfa$', rfa, re.IGNORECASE):
                continue

            # 2. Mandatory Valid 3D Preview: Strictly bypass any family without a genuine 3D thumbnail
            thumb_path = item.get("thumbnail")
            if not is_valid_3d_thumbnail(thumb_path):
                c1 = os.path.join(THUMBNAILS_DIR, code + ".png")
                c2 = os.path.join(LOCAL_CACHE_DIR, "Thumbnails", code + ".png")
                if is_valid_3d_thumbnail(c1):
                    thumb_path = c1
                    item["thumbnail"] = c1
                elif is_valid_3d_thumbnail(c2):
                    thumb_path = c2
                    item["thumbnail"] = c2
                else:
                    continue

            if not is_valid_3d_thumbnail(thumb_path):
                continue

            if self.current_discipline != "ALL" and item.get("discipline") != self.current_discipline:
                continue
            if self.current_category != "ALL" and item.get("category") != self.current_category:
                continue
            
            if query:
                title = item.get("title", "").lower()
                code_lower = code.lower()
                cat = item.get("category", "").lower()
                types_str = " ".join(item.get("types", [])).lower()
                if query not in title and query not in code_lower and query not in cat and query not in types_str:
                    continue

            self.filtered_families.append(item)

        self.TxtResultsCount.Text = u"{} Families Found".format(len(self.filtered_families))

        for fam in self.filtered_families:
            card = self.create_family_card(fam)
            self.LstFamilies.Items.Add(card)

    def create_family_card(self, fam):
        lbi = ListBoxItem()
        lbi.Tag = fam

        card_bg = SolidColorBrush(Color.FromRgb(32, 32, 36)) if self.is_dark_theme else SolidColorBrush(Color.FromRgb(255, 255, 255))
        img_bg = SolidColorBrush(Color.FromRgb(24, 24, 27)) if self.is_dark_theme else SolidColorBrush(Color.FromRgb(241, 245, 249))
        text_primary = SolidColorBrush(Color.FromRgb(244, 244, 245)) if self.is_dark_theme else SolidColorBrush(Color.FromRgb(15, 23, 42))
        text_muted = SolidColorBrush(Color.FromRgb(140, 140, 145)) if self.is_dark_theme else SolidColorBrush(Color.FromRgb(100, 116, 139))
        border_brush = self.Resources["BorderColor"]

        thumb_path = fam.get("thumbnail")
        if not is_valid_3d_thumbnail(thumb_path):
            code = fam.get("code", "")
            c1 = os.path.join(THUMBNAILS_DIR, code + ".png")
            c2 = os.path.join(LOCAL_CACHE_DIR, "Thumbnails", code + ".png")
            if is_valid_3d_thumbnail(c1):
                thumb_path = c1
            elif is_valid_3d_thumbnail(c2):
                thumb_path = c2
            else:
                thumb_path = None

        # ---------------- LIST VIEW MODE ----------------
        if self.view_mode == "List":
            card_border = Border()
            card_border.Width = 680
            card_border.Height = 44
            card_border.Background = card_bg
            card_border.BorderBrush = border_brush
            card_border.BorderThickness = Thickness(1)
            card_border.CornerRadius = System.Windows.CornerRadius(6)
            card_border.Padding = Thickness(8, 4, 8, 4)

            from System.Windows.Controls import Grid, ColumnDefinition
            row_grid = Grid()
            c0 = ColumnDefinition(); c0.Width = System.Windows.GridLength(40)
            c1 = ColumnDefinition(); c1.Width = System.Windows.GridLength(1, System.Windows.GridUnitType.Star)
            c2 = ColumnDefinition(); c2.Width = System.Windows.GridLength(140)
            c3 = ColumnDefinition(); c3.Width = System.Windows.GridLength(110)
            row_grid.ColumnDefinitions.Add(c0)
            row_grid.ColumnDefinitions.Add(c1)
            row_grid.ColumnDefinitions.Add(c2)
            row_grid.ColumnDefinitions.Add(c3)

            # Mini Thumbnail
            img_b = Border()
            img_b.Width = 32; img_b.Height = 32
            img_b.CornerRadius = System.Windows.CornerRadius(4)
            img_b.Background = img_bg
            img_b.ClipToBounds = True
            img = WpfImage()
            img.Stretch = System.Windows.Media.Stretch.Uniform
            if thumb_path and os.path.exists(thumb_path):
                bi = load_bitmap(thumb_path)
                if bi: img.Source = bi
            img_b.Child = img
            Grid.SetColumn(img_b, 0)
            row_grid.Children.Add(img_b)

            # Title & Code
            title_sp = StackPanel()
            title_sp.VerticalAlignment = System.Windows.VerticalAlignment.Center
            title_sp.Margin = Thickness(10, 0, 0, 0)
            txt_t = TextBlock()
            txt_t.Text = fam.get("title", fam.get("code", "Family"))
            txt_t.FontSize = 12; txt_t.FontWeight = System.Windows.FontWeights.Bold
            txt_t.Foreground = text_primary
            txt_t.TextTrimming = System.Windows.TextTrimming.CharacterEllipsis
            title_sp.Children.Add(txt_t)
            Grid.SetColumn(title_sp, 1)
            row_grid.Children.Add(title_sp)

            # Category
            txt_cat = TextBlock()
            txt_cat.Text = fam.get("category", "")
            txt_cat.FontSize = 11; txt_cat.FontWeight = System.Windows.FontWeights.SemiBold
            txt_cat.Foreground = SolidColorBrush(Color.FromRgb(128, 47, 45))
            txt_cat.VerticalAlignment = System.Windows.VerticalAlignment.Center
            txt_cat.TextTrimming = System.Windows.TextTrimming.CharacterEllipsis
            Grid.SetColumn(txt_cat, 2)
            row_grid.Children.Add(txt_cat)

            # Discipline Pill
            disc_b = Border()
            disc_b.CornerRadius = System.Windows.CornerRadius(4)
            disc_b.Background = SolidColorBrush(Color.FromRgb(24, 24, 27)) if self.is_dark_theme else SolidColorBrush(Color.FromRgb(241, 245, 249))
            disc_b.Padding = Thickness(6, 2, 6, 2)
            disc_b.VerticalAlignment = System.Windows.VerticalAlignment.Center
            disc_b.HorizontalAlignment = System.Windows.HorizontalAlignment.Left
            txt_disc = TextBlock()
            txt_disc.Text = fam.get("discipline", "")
            txt_disc.FontSize = 9.5; txt_disc.FontWeight = System.Windows.FontWeights.SemiBold
            txt_disc.Foreground = text_muted
            disc_b.Child = txt_disc
            Grid.SetColumn(disc_b, 3)
            row_grid.Children.Add(disc_b)

            card_border.Child = row_grid
            lbi.Content = card_border
            return lbi

        # ---------------- GRID VIEW MODES (ExtraLarge, Large, Medium, Small) ----------------
        if self.view_mode == "ExtraLarge":
            card_w = 230; card_h = 280; img_h = 175; font_title = 12; font_cat = 10
        elif self.view_mode == "Large":
            card_w = 185; card_h = 230; img_h = 135; font_title = 11.5; font_cat = 9.5
        elif self.view_mode == "Small":
            card_w = 120; card_h = 155; img_h = 75; font_title = 10; font_cat = 8.5
        else: # Medium (Default)
            card_w = 150; card_h = 190; img_h = 100; font_title = 11; font_cat = 9.5

        card_border = Border()
        card_border.Width = card_w
        card_border.Height = card_h
        card_border.Background = card_bg
        card_border.BorderBrush = border_brush
        card_border.BorderThickness = Thickness(1)
        card_border.CornerRadius = System.Windows.CornerRadius(8)
        card_border.Padding = Thickness(6)

        sp = StackPanel()

        # Thumbnail Container
        img_border = Border()
        img_border.Height = img_h
        img_border.CornerRadius = System.Windows.CornerRadius(6)
        img_border.Background = img_bg
        img_border.Margin = Thickness(0, 0, 0, 6)
        img_border.ClipToBounds = True

        img = WpfImage()
        img.Stretch = System.Windows.Media.Stretch.Uniform
        if thumb_path and os.path.exists(thumb_path):
            bi = load_bitmap(thumb_path)
            if bi:
                img.Source = bi
        img_border.Child = img
        sp.Children.Add(img_border)

        # Title
        txt_title = TextBlock()
        txt_title.Text = fam.get("title", fam.get("code", "Family"))
        txt_title.FontSize = font_title
        txt_title.FontWeight = System.Windows.FontWeights.Bold
        txt_title.Foreground = text_primary
        txt_title.TextTrimming = System.Windows.TextTrimming.CharacterEllipsis
        txt_title.MaxHeight = 30
        txt_title.TextWrapping = System.Windows.TextWrapping.Wrap
        sp.Children.Add(txt_title)

        # Category Badge
        txt_cat = TextBlock()
        txt_cat.Text = fam.get("category", "")
        txt_cat.FontSize = font_cat
        txt_cat.Foreground = SolidColorBrush(Color.FromRgb(128, 47, 45)) # Riyan Maroon
        txt_cat.FontWeight = System.Windows.FontWeights.SemiBold
        txt_cat.Margin = Thickness(0, 2, 0, 0)
        sp.Children.Add(txt_cat)

        card_border.Child = sp
        lbi.Content = card_border
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

        self.TxtDetailTitle.Text = fam.get("title", "")
        self.TxtDetailCode.Text = fam.get("code", "")
        self.TxtDetailDiscipline.Text = fam.get("discipline", "ARCHITECTURAL")
        self.TxtDetailCategory.Text = fam.get("category", "General")

        thumb_path = fam.get("thumbnail")
        if not is_valid_3d_thumbnail(thumb_path):
            code = fam.get("code", "")
            c1 = os.path.join(THUMBNAILS_DIR, code + ".png")
            c2 = os.path.join(LOCAL_CACHE_DIR, "Thumbnails", code + ".png")
            if is_valid_3d_thumbnail(c1):
                thumb_path = c1
            elif is_valid_3d_thumbnail(c2):
                thumb_path = c2
            else:
                thumb_path = None
        if thumb_path and is_valid_3d_thumbnail(thumb_path):
            self.ImgDetailPreview.Source = load_bitmap(thumb_path)
        else:
            self.ImgDetailPreview.Source = None

        # Graphic Capability Badges
        self.PanelBadges.Children.Clear()
        for b in fam.get("badges", []):
            badge_border = Border()
            badge_border.CornerRadius = System.Windows.CornerRadius(4)
            badge_border.Background = SolidColorBrush(Color.FromRgb(39, 39, 42)) if self.is_dark_theme else SolidColorBrush(Color.FromRgb(241, 245, 249))
            badge_border.Padding = Thickness(8, 4, 8, 4)
            badge_border.Margin = Thickness(0, 0, 6, 6)

            badge_sp = StackPanel()
            badge_sp.Orientation = System.Windows.Controls.Orientation.Horizontal

            ico = TextBlock()
            ico.Text = b.get("icon", "✔") + " "
            ico.FontSize = 10
            ico.Foreground = SolidColorBrush(Color.FromRgb(128, 47, 45)) # Riyan Maroon
            badge_sp.Children.Add(ico)

            lbl = TextBlock()
            lbl.Text = b.get("label", "")
            lbl.FontSize = 10
            lbl.FontWeight = System.Windows.FontWeights.SemiBold
            lbl.Foreground = SolidColorBrush(Color.FromRgb(228, 228, 231)) if self.is_dark_theme else SolidColorBrush(Color.FromRgb(15, 23, 42))
            badge_sp.Children.Add(lbl)

            badge_border.Child = badge_sp
            self.PanelBadges.Children.Add(badge_border)

        # Family Types Dropdown
        self.CmbTypes.Items.Clear()
        types = fam.get("types", ["Standard Type"])
        for t in types:
            self.CmbTypes.Items.Add(t)
        if self.CmbTypes.Items.Count > 0:
            self.CmbTypes.SelectedIndex = 0

        # Parameters Table
        self.PanelParams.Children.Clear()
        specs = fam.get("specs", {
            "Level Category": fam.get("category", "General"),
            "Operation": "Smart Parametric Controls",
            "Dimensions": "Width & Height Parametric",
            "Materials": "Configurable (Aluminium, Timber, Glass)"
        })
        for k, v in specs.items():
            row = StackPanel()
            row.Orientation = System.Windows.Controls.Orientation.Horizontal
            row.Margin = Thickness(0, 2, 0, 2)

            t_k = TextBlock()
            t_k.Text = k + ": "
            t_k.Width = 100
            t_k.FontSize = 11
            t_k.Foreground = SolidColorBrush(Color.FromRgb(113, 113, 122))
            row.Children.Add(t_k)

            t_v = TextBlock()
            t_v.Text = str(v)
            t_v.FontSize = 11
            t_v.FontWeight = System.Windows.FontWeights.SemiBold
            t_v.Foreground = SolidColorBrush(Color.FromRgb(244, 244, 245)) if self.is_dark_theme else SolidColorBrush(Color.FromRgb(15, 23, 42))
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
            ["1. 🔄 Sync Level Categories from Active RVT (Dilupa Master)",
             "2. 🔍 Audit & Standardize Family Materials (RYN_MAT Criteria)",
             "3. ⚡ Rebuild Catalog & Check Thumbnails",
             "4. 📂 Open SharePoint Library Folder"],
            message="Riyan Library Admin & Standards"
        )
        if not res:
            return

        if res.startswith("1."):
            self.sync_levels_from_active_doc()
        elif res.startswith("2."):
            self.audit_materials_interactive()
        elif res.startswith("3."):
            self.load_catalog_data()
            forms.alert(u"Catalog refreshed! Total: {} families.".format(len(self.catalog)), title=u"Catalog Refreshed")
        elif res.startswith("4."):
            try:
                subprocess.Popen(["explorer.exe", SHAREPOINT_LIB_ROOT])
            except:
                pass

    def audit_materials_interactive(self):
        if not DOC:
            forms.alert(u"No active Revit document open.\nPlease open your Library RVT first.", title=u"Audit Error")
            return
        
        import audit_materials
        self.TxtStatus.Text = u"Auditing Family Materials..."
        res = audit_materials.audit_document_materials(DOC)
        
        tot = res["total_families"]
        comp = len(res["compliant_families"])
        incons = len(res["inconsistent_materials"])
        miss = len(res["missing_parameters"])
        
        msg = u"Material Audit Completed for '{}'!\n\n".format(res["doc_title"])
        msg += u"• Total Families Scanned: {}\n".format(tot)
        msg += u"• Fully RYN_MAT Compliant: {}\n".format(comp)
        msg += u"• Non-Standard/Legacy Materials: {}\n".format(incons)
        msg += u"• Missing Expected Parameters: {}\n\n".format(miss)
        
        if miss > 0:
            msg += u"Sample Missing Parameters:\n"
            for item in res["missing_parameters"][:5]:
                msg += u" - {}: missing {}\n".format(item["family"], ", ".join(item["missing"]))
            msg += u"\n"
            
        if incons > 0:
            msg += u"Would you like to auto-standardize the {} families to official RYN_MAT materials now?".format(incons)
            if forms.alert(msg, yes=True, no=True):
                updated = audit_materials.apply_material_standardization(DOC, res)
                forms.alert(u"Standardization complete!\nUpdated {} material parameters to RYN_MAT standards.".format(updated), title=u"Standardized 👍")
        else:
            forms.alert(msg, title=u"Audit Results")

    def sync_levels_from_active_doc(self):
        """Reads all Levels from active RVT document and maps all hosted families to those levels!"""
        if not DOC:
            forms.alert(u"No active Revit document open.\nPlease open your Master Library RVT in Revit first.", title=u"Sync Error")
            return

        doc_title = DOC.Title
        forms.alert(u"Syncing Level categories from active document:\n{}\nThis will associate all families with their placement Level (e.g. Door-Sliding, Door-Swing...)".format(doc_title), title=u"Level Sync")

        levels = DB.FilteredElementCollector(DOC).OfClass(DB.Level).ToElements()
        if not levels:
            forms.alert(u"No levels found in active document.", title=u"Sync Error")
            return

        level_name_map = {}
        total_mapped = 0

        for lvl in levels:
            lvl_name = lvl.Name.strip()
            # Filter family instances hosted on this level
            lvl_filter = DB.ElementLevelFilter(lvl.Id)
            instances = DB.FilteredElementCollector(DOC).WherePasses(lvl_filter).WhereElementIsNotElementType().ToElements()
            for inst in instances:
                sym = getattr(inst, "Symbol", None)
                if sym and hasattr(sym, "Family"):
                    fam = sym.Family
                    if fam and not fam.IsInPlace:
                        level_name_map[fam.Name.upper()] = lvl_name
                        total_mapped += 1

        # Apply to catalog
        updated_count = 0
        for item in self.catalog:
            code = item.get("code", "").upper()
            if code in level_name_map:
                item["category"] = level_name_map[code]
                updated_count += 1

        # Save updated catalog
        try:
            save_path = os.path.join(CENTRAL_REPOSITORY, "catalog.json")
            with codecs.open(save_path, 'w', 'utf-8') as f:
                json.dump(self.catalog, f, indent=2)
            # Also cache
            cache_path = os.path.join(LOCAL_CACHE_DIR, "catalog.json")
            with codecs.open(cache_path, 'w', 'utf-8') as f:
                json.dump(self.catalog, f, indent=2)
            forms.alert(u"Successfully synced {} families directly from active RVT Levels!\nCatalog updated live.".format(updated_count), title=u"Sync Success 👍")
        except Exception as e:
            forms.alert(u"Catalog updated in memory, but error saving to disk:\n{}".format(str(e)), title=u"Save Warning")

        self.refresh_categories()
        self.apply_filter()

# -------------------------------------------------------------
# Entry Point
# -------------------------------------------------------------
if __name__ == "__main__":
    xaml_file = os.path.join(os.path.dirname(__file__), "ui.xaml")
    win = RiyanFamilyBrowser(xaml_file)
    win.ShowDialog()
