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
import re
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
from System.Windows import Window, WindowStartupLocation, Application, Visibility, Thickness, WindowState, Point
from System.Windows.Controls import ListBoxItem, Border, TextBlock, StackPanel, Image as WpfImage, Grid, ColumnDefinition
from System.Windows.Media import Brushes, Color, SolidColorBrush, ColorConverter, LinearGradientBrush, GradientStop
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
    try:
        from riyan_alert import show_alert
    except ImportError:
        _lib_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "lib"))
        if _lib_dir not in sys.path:
            sys.path.append(_lib_dir)
        from riyan_alert import show_alert
except Exception:
    DOC = None
    UIDOC = None
    APP = None
    try:
        from riyan_alert import show_alert
    except ImportError:
        _lib_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "lib"))
        if _lib_dir not in sys.path:
            sys.path.append(_lib_dir)
        from riyan_alert import show_alert

# -------------------------------------------------------------
# Configuration & Repository Locations
# -------------------------------------------------------------
SHAREPOINT_LIB_ROOT = os.path.expandvars(
    r"%USERPROFILE%\OneDrive - Riyan Private Limited\Riyan LK Projects - 00 - RIYAN REVIT STANDARD\02 LIBRARY"
)
CENTRAL_REPOSITORY = os.path.join(SHAREPOINT_LIB_ROOT, "00 RIYAN FAMILY REPOSITORY")
THUMBNAILS_DIR = os.path.join(CENTRAL_REPOSITORY, "Thumbnails")
# Look for Library_Cache dynamically in repo root (relative to script) or APPDATA
_this_dir = os.path.dirname(os.path.abspath(__file__))
_repo_root = os.path.abspath(os.path.join(_this_dir, "..", "..", "..", ".."))
_repo_cache = os.path.join(_repo_root, "Library_Cache")
if os.path.exists(_repo_cache):
    LOCAL_CACHE_DIR = _repo_cache
else:
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

def resolve_live_path(path_str):
    if not path_str:
        return None
    try:
        if os.path.exists(path_str):
            return path_str
    except Exception:
        pass
    
    user_prof = os.path.expandvars(r"%USERPROFILE%")
    
    # 1. Adapt OneDrive - Riyan Private Limited paths
    onedrive_tag = "OneDrive - Riyan Private Limited"
    if onedrive_tag in path_str:
        idx = path_str.find(onedrive_tag)
        rel_part = path_str[idx + len(onedrive_tag):].lstrip("\\/")
        cand = os.path.join(user_prof, onedrive_tag, rel_part)
        try:
            if os.path.exists(cand):
                return cand
        except Exception:
            pass
            
    # 2. Adapt C:\Users\<old_user>\... to current %USERPROFILE%
    parts = path_str.split(os.sep)
    if len(parts) > 3 and parts[0].endswith(":") and parts[1].lower() == "users":
        cand_user = os.path.join(user_prof, *parts[3:])
        try:
            if os.path.exists(cand_user):
                return cand_user
        except Exception:
            pass

    return None

# -------------------------------------------------------------
# In-Memory Fast Thumbnail Cache (Eliminates 7,000+ disk checks)
# -------------------------------------------------------------
_THUMB_CACHE_LOCAL = {}
_THUMB_CACHE_CENTRAL = {}
_THUMB_CACHE_INIT = False

def init_thumbnail_cache():
    global _THUMB_CACHE_LOCAL, _THUMB_CACHE_CENTRAL, _THUMB_CACHE_INIT
    if _THUMB_CACHE_INIT:
        return
    try:
        loc_dir = os.path.join(LOCAL_CACHE_DIR, "Thumbnails")
        if os.path.isdir(loc_dir):
            for f in os.listdir(loc_dir):
                if f.lower().endswith(".png"):
                    _THUMB_CACHE_LOCAL[f.lower()] = os.path.join(loc_dir, f)
    except Exception:
        pass
    try:
        if os.path.isdir(THUMBNAILS_DIR):
            for f in os.listdir(THUMBNAILS_DIR):
                if f.lower().endswith(".png"):
                    _THUMB_CACHE_CENTRAL[f.lower()] = os.path.join(THUMBNAILS_DIR, f)
    except Exception:
        pass
    _THUMB_CACHE_INIT = True

def resolve_thumbnail_path(fam_item):
    if not fam_item:
        return None
    init_thumbnail_cache()
    code = fam_item.get("code", "")
    key = (code + ".png").lower()
    
    # 1. Check local cache (fastest)
    if key in _THUMB_CACHE_LOCAL:
        return _THUMB_CACHE_LOCAL[key]
        
    # 2. Check central repo
    if key in _THUMB_CACHE_CENTRAL:
        return _THUMB_CACHE_CENTRAL[key]

    # 3. Fallback to existing path if valid
    t = fam_item.get("thumbnail")
    if t and is_valid_3d_thumbnail(t):
        return t

    return None

def is_sub_component(item):
    """
    Identifies internal nested/sub-component families loaded inside other families
    (such as hardware pull handles, hinges, door panels, window panels, profile .rfa files).
    These are strictly filtered out so they do not clutter project family browser.
    """
    if not item:
        return False
    path = item.get("rfa_path", "").replace("/", "\\")
    code = item.get("code", "")
    
    # 1. Check folder directory names
    parts = [p.strip().lower() for p in path.split("\\")]
    for p in parts[:-1]:
        if p in ["profile", "profiles", "door panel", "glass panel", "awning panel", "support profile", "baluster profile"]:
            return True
            
    # 2. Check profile naming patterns
    if re.search(r'(_pro_|_profile_|profile$|^profile\b|^section profile|^architrave_profile|^c shapes-profile|^gutter profile)', code, re.IGNORECASE):
        return True
        
    # 3. Check hardware / handles / hinges / brackets
    if re.search(r'(hardware|handle[std0-9]*$|^hafele\b|^pivot hinge|^stair_hardware)', code, re.IGNORECASE):
        if not any(k in code.lower() for k in ["cabinet", "table", "chair", "wardrobe"]):
            return True
            
    # 4. Check standalone nested panel piece patterns
    if re.match(r'^(door\s*panel|w\s*panel|top\s*panel|mid\s*panel|louver\s*panel|glass\s*panel|panel\s*2|panel\s*with\s*glass|sliding\s*front\s*panel|sliding_door_panel|st-door\s*panel|vv-w_fg\s*-\s*panel|top\s*window\s*panel)', code, re.IGNORECASE):
        return True
        
    return False

def get_family_priority(item):
    """
    Prioritizes Dilupa's Riyan standard families and Level families at the front:
    Rank 0: Families/Walls placed on Dilupa's Master Levels (is_level_master == True)
    Rank 1: Dilupa's Riyan standard families (RYN_ prefix) in curated Level categories
    Rank 2: RYN_ families in other categories
    Rank 3: Standard families in curated Level categories
    Rank 4: Generic *-Other families
    """
    code = item.get("code", "")
    cat = item.get("category", "")
    is_level_master = 0 if item.get("is_level_master") else 1
    is_ryn = 0 if code.upper().startswith("RYN_") else 1
    is_other = 1 if ("-other" in cat.lower() or "other" in cat.lower()) else 0
    return (is_level_master, is_ryn, is_other, code.lower())

def category_sort_key(cat_name):
    """
    Sorts curated Level categories first, and puts generic '*-Other' categories at the bottom.
    """
    is_other = 1 if ("-other" in cat_name.lower() or "other" in cat_name.lower()) else 0
    return (is_other, cat_name)

def resolve_family_path(fam):
    if not fam:
        return None
    rfa = fam.get("rfa_path", "")
    try:
        if rfa and os.path.exists(rfa):
            return rfa
    except Exception:
        pass
        
    code = fam.get("code", "")
    code_rfa = code + ".rfa" if not code.lower().endswith(".rfa") else code
    
    # 1. Try adapting path
    resolved = resolve_live_path(rfa)
    try:
        if resolved and os.path.exists(resolved):
            return resolved
    except Exception:
        pass
        
    # 2. Check under SharePoint library root and cache
    sp_candidates = [
        os.path.join(CENTRAL_REPOSITORY, code_rfa),
        os.path.join(SHAREPOINT_LIB_ROOT, code_rfa),
        os.path.join(LOCAL_CACHE_DIR, "Families", code_rfa)
    ]
    for cand in sp_candidates:
        try:
            if os.path.exists(cand):
                return cand
        except Exception:
            pass
            
    # 3. Search SharePoint library root if folder exists
    try:
        if os.path.exists(SHAREPOINT_LIB_ROOT):
            for root, dirs, files in os.walk(SHAREPOINT_LIB_ROOT):
                for f in files:
                    if f.lower() == code_rfa.lower():
                        return os.path.join(root, f)
    except Exception:
        pass
                
    return None

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
        elif "WALL" in name_upper or "WALL" in dir_upper or "FACADE" in name_upper or "FACADE" in dir_upper:
            if not any(k in name_upper.lower() for k in ["toilet", "lavatory", "shower", "sink", "fountain", "washfountain", "urinal", "lighting", "light", "tag", "drain", "tree", "plant", "container", "hute", "door", "window"]):
                cat = "Walls"
            else:
                cat = "Arch-Other"
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
        if hasattr(self, "BtnMaximize") and self.BtnMaximize:
            self.BtnMaximize.Click += self.on_maximize_restore
        self.BtnAdminSync.Click += self.on_admin_sync
        self.BtnToggleTheme.Click += self.on_toggle_theme
        self.TitleBar.MouseLeftButtonDown += self.on_titlebar_mouse_down

        # Window Drag Resizing Handlers
        if hasattr(self, "ResizeRightThumb") and self.ResizeRightThumb:
            self.ResizeRightThumb.DragDelta += self.on_resize_right
        if hasattr(self, "ResizeBottomThumb") and self.ResizeBottomThumb:
            self.ResizeBottomThumb.DragDelta += self.on_resize_bottom
        if hasattr(self, "ResizeGripThumb") and self.ResizeGripThumb:
            self.ResizeGripThumb.DragDelta += self.on_resize_bottom_right

        self.TxtSearch.TextChanged += self.on_search_changed
        self.LstCategories.SelectionChanged += self.on_category_changed
        self.LstFamilies.SelectionChanged += self.on_family_selected

        # Mouse Wheel Anywhere Scrolling Support & Incremental Lazy-Loading on Scroll
        self.rendered_count = 0
        if hasattr(self, "CardsScrollViewer") and self.CardsScrollViewer:
            self.CardsScrollViewer.PreviewMouseWheel += self.on_cards_preview_mouse_wheel
            self.CardsScrollViewer.ScrollChanged += self.on_cards_scroll_changed
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
            env_uname = os.environ.get("USERNAME", "").lower()
            ADMIN_USERS = ["user", "windows", "dilupa", "dilupa.chathuranga", "dilupac", "dilupa1990"]
            self.is_admin = (uname in ADMIN_USERS) or (env_uname in ADMIN_USERS)
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

        self.update_discipline_tab_styles()

        # Load Catalog Data (Single Fast Pass)
        self._is_loading = True
        self.load_catalog_data()
        self._is_loading = False

    def on_titlebar_mouse_down(self, sender, e):
        try:
            if hasattr(e, "ClickCount") and e.ClickCount == 2:
                self.on_maximize_restore(sender, e)
            else:
                self.DragMove()
        except Exception:
            pass

    def on_maximize_restore(self, sender=None, e=None):
        try:
            if self.WindowState == WindowState.Maximized:
                self.WindowState = WindowState.Normal
                if hasattr(self, "BtnMaximize") and self.BtnMaximize:
                    self.BtnMaximize.Content = u"🗖"
            else:
                self.WindowState = WindowState.Maximized
                if hasattr(self, "BtnMaximize") and self.BtnMaximize:
                    self.BtnMaximize.Content = u"🗗"
        except Exception:
            pass

    def on_resize_right(self, sender, e):
        try:
            new_w = self.ActualWidth + e.HorizontalChange
            if new_w >= self.MinWidth:
                self.Width = new_w
        except Exception:
            pass

    def on_resize_bottom(self, sender, e):
        try:
            new_h = self.ActualHeight + e.VerticalChange
            if new_h >= self.MinHeight:
                self.Height = new_h
        except Exception:
            pass

    def on_resize_bottom_right(self, sender, e):
        try:
            new_w = self.ActualWidth + e.HorizontalChange
            new_h = self.ActualHeight + e.VerticalChange
            if new_w >= self.MinWidth:
                self.Width = new_w
            if new_h >= self.MinHeight:
                self.Height = new_h
        except Exception:
            pass

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
            self.Resources["HoverBg"] = SolidColorBrush(Color.FromRgb(42, 42, 48))
            self.Resources["HoverBorder"] = SolidColorBrush(Color.FromRgb(63, 63, 70))
            grad_dark = LinearGradientBrush()
            grad_dark.StartPoint = Point(0, 0)
            grad_dark.EndPoint = Point(1, 1)
            grad_dark.GradientStops.Add(GradientStop(Color.FromRgb(37, 37, 42), 0.0))
            grad_dark.GradientStops.Add(GradientStop(Color.FromRgb(22, 22, 25), 1.0))
            self.Resources["ThumbnailBg"] = grad_dark
            self.Resources["ThumbnailBorder"] = SolidColorBrush(Color.FromRgb(46, 46, 54))
            self.Background = Brushes.Transparent
            self.Foreground = self.Resources["TextPrimary"]
        else:
            self.BtnToggleTheme.Content = u"☀️ Light"
            self.Resources["WindowBg"] = SolidColorBrush(Color.FromRgb(248, 250, 252)) # Slate 50
            self.Resources["SurfaceBg"] = SolidColorBrush(Color.FromRgb(255, 255, 255))
            self.Resources["CardBg"] = SolidColorBrush(Color.FromRgb(255, 255, 255))
            self.Resources["BorderColor"] = SolidColorBrush(Color.FromRgb(203, 213, 225)) # Slate 300
            self.Resources["HoverBg"] = SolidColorBrush(Color.FromRgb(226, 232, 240))     # Slate 200 distinct hover
            self.Resources["HoverBorder"] = SolidColorBrush(Color.FromRgb(203, 213, 225)) # Slate 300
            self.Resources["TextPrimary"] = SolidColorBrush(Color.FromRgb(15, 23, 42))     # Deep Pitch Black/Slate
            self.Resources["TextSecondary"] = SolidColorBrush(Color.FromRgb(51, 65, 85))   # Dark Slate 700
            self.Resources["TextMuted"] = SolidColorBrush(Color.FromRgb(100, 116, 139))   # Slate 500
            grad_light = LinearGradientBrush()
            grad_light.StartPoint = Point(0, 0)
            grad_light.EndPoint = Point(1, 1)
            grad_light.GradientStops.Add(GradientStop(Color.FromRgb(248, 250, 252), 0.0))
            grad_light.GradientStops.Add(GradientStop(Color.FromRgb(235, 239, 245), 1.0))
            self.Resources["ThumbnailBg"] = grad_light
            self.Resources["ThumbnailBorder"] = SolidColorBrush(Color.FromRgb(215, 222, 232))
            self.Background = Brushes.Transparent
            self.Foreground = self.Resources["TextPrimary"]

        # Controls text contrast - strictly enforce white on selected discipline tab!
        self.update_discipline_tab_styles()

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

    def update_discipline_tab_styles(self):
        white_brush = SolidColorBrush(Color.FromRgb(255, 255, 255))
        unselected_brush = self.Resources["TextSecondary"]
        for rb in [self.TabAll, self.TabArc, self.TabStr, self.TabPlumb, self.TabElec, self.TabFire, self.TabAcmv]:
            if rb:
                if rb.IsChecked:
                    rb.Foreground = white_brush
                else:
                    rb.Foreground = unselected_brush

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
            self.TxtStatus.Text = u"Riyan Library (Local Cache Mode)"

        if target_path:
            try:
                with codecs.open(target_path, 'r', 'utf-8-sig') as f:
                    raw_items = json.load(f)
                    import re
                    # Strict Zero-Backup Filter (Eliminate .0001, .0002 backup copies)
                    self.catalog = []
                    for item in raw_items:
                        c = item.get("code", "")
                        r = item.get("rfa_path", "")
                        if re.search(r'\.\d{3,4}$', c) or re.search(r'\.\d{3,4}\.rfa$', r, re.IGNORECASE):
                            continue
                        
                        # Strict Filter: Exclude internal nested sub-components (hardware, profiles, loose panels)
                        if is_sub_component(item):
                            continue

                        # Resolve thumbnail across local, repo, or OneDrive
                        item["thumbnail"] = resolve_thumbnail_path(item)
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
                        
                        # Strict Filter: Exclude internal nested sub-components
                        if is_sub_component({"code": fn_clean, "rfa_path": p}):
                            continue
                        
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
        self.update_discipline_tab_styles()
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
        white_brush = SolidColorBrush(Color.FromRgb(255, 255, 255))
        normal_brush = self.Resources["TextPrimary"]

        all_item = ListBoxItem()
        all_item.Content = u"All Categories ({})".format(total)
        all_item.Tag = "ALL"
        all_item.Foreground = white_brush
        self.LstCategories.Items.Add(all_item)
        all_item.IsSelected = True

        for cat in sorted(counts.keys(), key=category_sort_key):
            lbi = ListBoxItem()
            lbi.Content = u"{} ({})".format(cat, counts[cat])
            lbi.Tag = cat
            lbi.Foreground = normal_brush
            self.LstCategories.Items.Add(lbi)

    def on_category_changed(self, sender, e):
        if getattr(self, "_is_loading", False):
            return
        sel = self.LstCategories.SelectedItem
        if sel and hasattr(sel, "Tag"):
            self.current_category = sel.Tag
        else:
            self.current_category = "ALL"

        # Strict Selection Contrast: Force white text on active category
        white_brush = SolidColorBrush(Color.FromRgb(255, 255, 255))
        normal_brush = self.Resources["TextPrimary"]
        for i in range(self.LstCategories.Items.Count):
            item = self.LstCategories.Items[i]
            if item == sel or (hasattr(item, "IsSelected") and item.IsSelected):
                item.Foreground = white_brush
            else:
                item.Foreground = normal_brush

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

        # Smart Prioritization: Dilupa's RYN_ families & Level families at the front!
        self.filtered_families.sort(key=get_family_priority)

        self.TxtResultsCount.Text = u"{} Families Found".format(len(self.filtered_families))

        # Instant Open: Render first batch (48 cards) immediately, lazy-load remaining on scroll
        self.rendered_count = 0
        self.load_next_card_batch(48)
        if hasattr(self, "CardsScrollViewer") and self.CardsScrollViewer:
            self.CardsScrollViewer.ScrollToTop()

    def load_next_card_batch(self, count=36):
        if not hasattr(self, "filtered_families") or not self.filtered_families:
            return
        total = len(self.filtered_families)
        start_idx = getattr(self, "rendered_count", 0)
        if start_idx >= total:
            return
        end_idx = min(start_idx + count, total)
        for i in range(start_idx, end_idx):
            card = self.create_family_card(self.filtered_families[i])
            self.LstFamilies.Items.Add(card)
        self.rendered_count = end_idx

    def on_cards_scroll_changed(self, sender, e):
        try:
            if getattr(self, "rendered_count", 0) < len(self.filtered_families):
                if e.VerticalOffset + e.ViewportHeight >= e.ExtentHeight - 400:
                    self.load_next_card_batch(36)
        except Exception:
            pass

    def create_family_card(self, fam):
        lbi = ListBoxItem()
        lbi.Tag = fam

        card_bg = SolidColorBrush(Color.FromRgb(32, 32, 36)) if self.is_dark_theme else SolidColorBrush(Color.FromRgb(255, 255, 255))
        img_bg = SolidColorBrush(Color.FromRgb(24, 24, 27)) if self.is_dark_theme else SolidColorBrush(Color.FromRgb(241, 245, 249))
        text_primary = SolidColorBrush(Color.FromRgb(244, 244, 245)) if self.is_dark_theme else SolidColorBrush(Color.FromRgb(15, 23, 42))
        text_muted = SolidColorBrush(Color.FromRgb(140, 140, 145)) if self.is_dark_theme else SolidColorBrush(Color.FromRgb(100, 116, 139))
        border_brush = self.Resources["BorderColor"]

        thumb_path = fam.get("thumbnail")
        if not thumb_path or not is_valid_3d_thumbnail(thumb_path):
            thumb_path = resolve_thumbnail_path(fam)
            fam["thumbnail"] = thumb_path

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

            row_grid = Grid()
            c0 = ColumnDefinition(); c0.Width = System.Windows.GridLength(40)
            c1 = ColumnDefinition(); c1.Width = System.Windows.GridLength(1, System.Windows.GridUnitType.Star)
            c2 = ColumnDefinition(); c2.Width = System.Windows.GridLength(140)
            c3 = ColumnDefinition(); c3.Width = System.Windows.GridLength(110)
            row_grid.ColumnDefinitions.Add(c0)
            row_grid.ColumnDefinitions.Add(c1)
            row_grid.ColumnDefinitions.Add(c2)
            row_grid.ColumnDefinitions.Add(c3)

            # Mini Thumbnail or Initial Badge
            img_b = Border()
            img_b.Width = 32; img_b.Height = 32
            img_b.CornerRadius = System.Windows.CornerRadius(4)
            img_b.Background = self.Resources["ThumbnailBg"]
            img_b.BorderBrush = self.Resources["ThumbnailBorder"]
            img_b.BorderThickness = Thickness(1)
            img_b.ClipToBounds = True
            
            bi = load_bitmap(thumb_path) if (thumb_path and os.path.exists(thumb_path)) else None
            if bi:
                img = WpfImage()
                img.Stretch = System.Windows.Media.Stretch.Uniform
                img.Source = bi
                img_b.Child = img
            else:
                txt_init = TextBlock()
                cat_up = fam.get("category", "").upper()
                init_letter = "R"
                if "DOOR" in cat_up: init_letter = "D"
                elif "WINDOW" in cat_up: init_letter = "W"
                elif "TITLE" in cat_up: init_letter = "T"
                elif "COLUMN" in cat_up or "BEAM" in cat_up or fam.get("discipline") == "STRUCTURAL": init_letter = "S"
                elif "PLUMB" in cat_up or fam.get("discipline") == "PLUMBING": init_letter = "P"
                elif "ELEC" in cat_up or fam.get("discipline") == "ELECTRICAL": init_letter = "E"
                elif "ACMV" in cat_up or fam.get("discipline") == "ACMV": init_letter = "M"
                
                txt_init.Text = init_letter
                txt_init.FontSize = 13
                txt_init.FontWeight = System.Windows.FontWeights.Bold
                txt_init.Foreground = SolidColorBrush(Color.FromRgb(128, 47, 45))
                txt_init.HorizontalAlignment = System.Windows.HorizontalAlignment.Center
                txt_init.VerticalAlignment = System.Windows.VerticalAlignment.Center
                img_b.Child = txt_init

            Grid.SetColumn(img_b, 0)
            row_grid.Children.Add(img_b)

            # Title & Code
            title_sp = StackPanel()
            title_sp.VerticalAlignment = System.Windows.VerticalAlignment.Center
            title_sp.Margin = Thickness(10, 0, 0, 0)
            txt_t = TextBlock()
            txt_t.Text = fam.get("code", fam.get("title", "Family"))
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
        img_border.Background = self.Resources["ThumbnailBg"]
        img_border.BorderBrush = self.Resources["ThumbnailBorder"]
        img_border.BorderThickness = Thickness(1)
        img_border.Margin = Thickness(0, 0, 0, 6)
        img_border.ClipToBounds = True

        bi = load_bitmap(thumb_path) if (thumb_path and os.path.exists(thumb_path)) else None
        if bi:
            img = WpfImage()
            img.Stretch = System.Windows.Media.Stretch.Uniform
            img.Margin = Thickness(3)
            img.Source = bi
            img_border.Child = img
        else:
            fallback_grid = Grid()
            inner_bg = SolidColorBrush(Color.FromRgb(30, 30, 34)) if self.is_dark_theme else SolidColorBrush(Color.FromRgb(240, 243, 246))
            accent_border = Border()
            accent_border.CornerRadius = System.Windows.CornerRadius(6)
            accent_border.Background = inner_bg
            fallback_grid.Children.Add(accent_border)
            
            fb_sp = StackPanel()
            fb_sp.VerticalAlignment = System.Windows.VerticalAlignment.Center
            fb_sp.HorizontalAlignment = System.Windows.HorizontalAlignment.Center
            
            cat_str = fam.get("category", "").upper()
            disc_str = fam.get("discipline", "").upper()
            
            badge_text = "RYAN"
            sub_text = "STANDARD"
            if "DOOR" in cat_str:
                badge_text = "DOOR"
                sub_text = "FAMILY"
            elif "WINDOW" in cat_str:
                badge_text = "WINDOW"
                sub_text = "FAMILY"
            elif "WALL" in cat_str:
                badge_text = "WALL"
                sub_text = "ARCHITECTURAL"
            elif "TITLEBLOCK" in cat_str:
                badge_text = "TITLE BLOCK"
                sub_text = "SHEET"
            elif "COLUMN" in cat_str:
                badge_text = "COLUMN"
                sub_text = "STRUCTURAL"
            elif "BEAM" in cat_str or "FRAME" in cat_str or disc_str == "STRUCTURAL":
                badge_text = "STRUCTURE"
                sub_text = "FRAME"
            elif "PLUMB" in cat_str or disc_str == "PLUMBING":
                badge_text = "PLUMBING"
                sub_text = "FIXTURE"
            elif "ELEC" in cat_str or disc_str == "ELECTRICAL":
                badge_text = "ELECTRICAL"
                sub_text = "EQUIPMENT"
            elif "ACMV" in cat_str or "DUCT" in cat_str or disc_str == "ACMV":
                badge_text = "HVAC / ACMV"
                sub_text = "MECHANICAL"
                
            pill_b = Border()
            pill_b.CornerRadius = System.Windows.CornerRadius(4)
            pill_b.Background = SolidColorBrush(Color.FromRgb(128, 47, 45))
            pill_b.Padding = Thickness(6, 2, 6, 2)
            pill_b.HorizontalAlignment = System.Windows.HorizontalAlignment.Center
            
            txt_pill = TextBlock()
            txt_pill.Text = badge_text
            txt_pill.FontSize = 10 if self.view_mode in ["ExtraLarge", "Large"] else 8.5
            txt_pill.FontWeight = System.Windows.FontWeights.Bold
            txt_pill.Foreground = SolidColorBrush(Color.FromRgb(255, 255, 255))
            pill_b.Child = txt_pill
            fb_sp.Children.Add(pill_b)
            
            txt_sub = TextBlock()
            txt_sub.Text = sub_text
            txt_sub.FontSize = 8.5 if self.view_mode in ["ExtraLarge", "Large"] else 7.5
            txt_sub.FontWeight = System.Windows.FontWeights.SemiBold
            txt_sub.Foreground = text_muted
            txt_sub.Margin = Thickness(0, 4, 0, 0)
            txt_sub.HorizontalAlignment = System.Windows.HorizontalAlignment.Center
            fb_sp.Children.Add(txt_sub)
            
            fallback_grid.Children.Add(fb_sp)
            img_border.Child = fallback_grid

        sp.Children.Add(img_border)

        # Title (Strictly preserve user's actual family name / code)
        txt_title = TextBlock()
        txt_title.Text = fam.get("code", fam.get("title", "Family"))
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

        fam_name = fam.get("code", fam.get("title", ""))
        self.TxtDetailTitle.Text = fam_name
        self.TxtDetailCode.Text = fam.get("category", "General")
        self.TxtDetailDiscipline.Text = fam.get("discipline", "ARCHITECTURAL")
        self.TxtDetailCategory.Text = fam.get("category", "General")

        thumb_path = fam.get("thumbnail")
        if not thumb_path or not is_valid_3d_thumbnail(thumb_path):
            thumb_path = resolve_thumbnail_path(fam)
            fam["thumbnail"] = thumb_path
        if thumb_path and is_valid_3d_thumbnail(thumb_path):
            self.ImgDetailPreview.Source = load_bitmap(thumb_path)
        else:
            self.ImgDetailPreview.Source = None

        # Graphic Capability Badges
        self.PanelBadges.Children.Clear()
        for b in fam.get("badges", []):
            bd = Border()
            bd.CornerRadius = System.Windows.CornerRadius(4)
            bd.Background = SolidColorBrush(ColorConverter.ConvertFromString(b.get("bg", "#475569")))
            bd.Padding = Thickness(6, 2, 6, 2)
            bd.Margin = Thickness(0, 0, 4, 4)

            sp_b = StackPanel()
            sp_b.Orientation = System.Windows.Controls.Orientation.Horizontal

            t_lbl = TextBlock()
            t_lbl.Text = b.get("label", "")
            t_lbl.FontSize = 10
            t_lbl.FontWeight = System.Windows.FontWeights.SemiBold
            t_lbl.Foreground = SolidColorBrush(Color.FromRgb(255, 255, 255))
            sp_b.Children.Add(t_lbl)
            bd.Child = sp_b
            self.PanelBadges.Children.Add(bd)

        # Family Types Dropdown
        self.CmbTypes.Items.Clear()
        types = fam.get("types", ["Standard Type"])
        for t in types:
            self.CmbTypes.Items.Add(t)
        if self.CmbTypes.Items.Count > 0:
            self.CmbTypes.SelectedIndex = 0

        # Specifications & Parameters Panel
        self.PanelParams.Children.Clear()
        specs = fam.get("specs", {
            "Discipline": fam.get("discipline", "ARCHITECTURAL"),
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

    def load_family_from_master_rvt(self, fam_item):
        """Attempts to load and overwrite family directly from Master Library RVT."""
        fam_name = fam_item.get("code", fam_item.get("title", ""))
        source_path = fam_item.get("source_doc_path", r"D:\RIYAN\TEMPLATES\MODEL\RIYAN - LIBRARY FILE.rvt")
        source_doc = None
        need_close = False
        try:
            if hasattr(APP, "Documents"):
                for d in APP.Documents:
                    if (d.PathName and source_path and d.PathName.lower() == source_path.lower()) or d.Title == "RIYAN - LIBRARY FILE":
                        source_doc = d
                        break
        except:
            pass

        if not source_doc and os.path.exists(source_path):
            try:
                source_doc = APP.OpenDocumentFile(source_path)
                need_close = True
            except:
                pass

        if not source_doc:
            return False

        try:
            # Find Family in source_doc
            target_fam = None
            for f in DB.FilteredElementCollector(source_doc).OfClass(DB.Family):
                if f.Name.upper() == fam_name.upper():
                    target_fam = f
                    break

            if not target_fam:
                return False

            # Open in memory and load into DOC with overwrite
            fam_doc = source_doc.EditFamily(target_fam)
            if fam_doc:
                handler = FamilyLoadHandler()
                t = DB.Transaction(DOC, "Load Riyan Family from Master: " + fam_name)
                t.Start()
                success = fam_doc.LoadFamily(DOC, handler)
                t.Commit()
                fam_doc.Close(False)
                if success:
                    self.TxtStatus.Text = u"Loaded from Master RVT: {}".format(fam_name)
                    show_alert(u"Family '{}' was successfully loaded and overwritten directly from the Master Library RVT!".format(fam_name), 
                               title=u"Family Loaded from Master 👍", is_error=False)
                    return True
        except Exception as ex:
            pass
        finally:
            if need_close and source_doc:
                try: source_doc.Close(False)
                except: pass
        return False

    def on_load_family(self, sender, e):
        if not self.selected_family:
            show_alert(u"Please select a family from the list to load.", title=u"Load Family", is_warning=True)
            return
        
        # 1. Handle System Wall Types (copied directly from Master Library RVT)
        if self.selected_family.get("is_system_family") or self.selected_family.get("system_type") == "Wall":
            self.load_system_wall(self.selected_family)
            return

        rfa_path = resolve_family_path(self.selected_family)
        if not rfa_path or not os.path.exists(rfa_path):
            # Try loading directly from Master RVT document!
            loaded_from_master = self.load_family_from_master_rvt(self.selected_family)
            if loaded_from_master:
                return

            code_name = self.selected_family.get("code", self.selected_family.get("title", "Family"))
            msg = u"Family '{}' could not be found locally.\n\n".format(code_name)
            msg += u"Source Repository:\nOneDrive - Riyan Private Limited\\...\\02 LIBRARY\n\n"
            msg += u"To load this family on your laptop:\n"
            msg += u"1. Open OneDrive and ensure the '02 LIBRARY' folder is synced to your PC.\n"
            msg += u"2. Once synced, click 'Load' again to load directly into Revit."
            show_alert(msg, title=u"Riyan Family - OneDrive Sync Required", is_warning=True)
            return

        if not DOC:
            show_alert(u"No active Revit document found.", title=u"Revit Document", is_error=True)
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
            show_alert(u"Family '{}' was successfully loaded and overwritten into the active project!".format(fam_name), 
                       title=u"Family Loaded 👍", is_error=False)
        except Exception as ex:
            show_alert(u"Failed to load family:\n{}".format(str(ex)), title=u"Load Error", is_error=True)
        finally:
            self.Topmost = False

    def load_system_wall(self, fam_item):
        """Loads/Copies a System Wall Type from Master Library RVT into active project document with clean 100% overwrite."""
        if not DOC:
            show_alert(u"No active Revit document open.", title=u"Load Error", is_error=True)
            return
            
        wall_name = fam_item.get("code", fam_item.get("title", ""))
        source_path = fam_item.get("source_doc_path", "")
        
        # 1. If currently active doc is the Master Library itself
        if DOC.Title == fam_item.get("source_doc_title") or (DOC.PathName and source_path and DOC.PathName.lower() == source_path.lower()):
            show_alert(u"You are currently working directly inside the Master Library RVT where this wall resides.", title=u"Master RVT Active", is_warning=True)
            return

        # 2. Locate Master RVT document (either already open in background, or open temporarily)
        source_doc = None
        need_close = False
        try:
            if hasattr(APP, "Documents"):
                for d in APP.Documents:
                    if d.PathName and source_path and d.PathName.lower() == source_path.lower():
                        source_doc = d
                        break
                    elif d.Title == fam_item.get("source_doc_title"):
                        source_doc = d
                        break
        except:
            pass

        if not source_doc:
            candidates = [
                source_path,
                r"D:\RIYAN\TEMPLATES\MODEL\RIYAN - LIBRARY FILE.rvt",
                os.path.join(SHAREPOINT_LIB_ROOT, "RIYAN - LIBRARY FILE.rvt")
            ]
            for cand in candidates:
                if cand and os.path.exists(cand):
                    try:
                        source_doc = APP.OpenDocumentFile(cand)
                        need_close = True
                        break
                    except:
                        pass

        if not source_doc:
            show_alert(u"Could not access Master Library RVT file:\n{}\nPlease ensure 'RIYAN - LIBRARY FILE.rvt' is available.".format(source_path), 
                       title=u"Master RVT Required", is_error=True)
            return

        # 3. Find WallType in source Master RVT
        source_types = DB.FilteredElementCollector(source_doc).OfClass(DB.WallType).ToElements()
        target_type = None
        for st in source_types:
            try:
                name = DB.Element.Name.GetValue(st)
            except:
                name = getattr(st, "Name", "")
            if name.upper() == wall_name.upper():
                target_type = st
                break

        if not target_type:
            if need_close:
                try: source_doc.Close(False)
                except: pass
            show_alert(u"Wall Type '{}' was not found in Master Library RVT.".format(wall_name), title=u"Wall Type Not Found", is_error=True)
            return

        # 4. Check if WallType is already loaded in active project for Clean Overwrite
        existing_types = [t for t in DB.FilteredElementCollector(DOC).OfClass(DB.WallType).ToElements() 
                          if DB.Element.Name.GetValue(t).upper() == wall_name.upper()]
        old_type = existing_types[0] if existing_types else None

        # 5. Copy WallType into active document with 100% clean overwrite
        self.Topmost = True
        try:
            t = DB.Transaction(DOC, "Load Riyan Wall: " + wall_name)
            t.Start()

            # Temporarily rename old type to avoid duplicate naming conflict during CopyElements
            temp_old_name = wall_name + "_OLD_TEMP_" + str(System.Guid.NewGuid())[:8]
            if old_type:
                try:
                    old_type.Name = temp_old_name
                except Exception:
                    pass

            copy_opts = DB.CopyPasteOptions()
            id_list = List[DB.ElementId]()
            id_list.Add(target_type.Id)
            copied_ids = DB.ElementTransformUtils.CopyElements(source_doc, id_list, DOC, None, copy_opts)

            # Locate the newly copied master wall type
            new_type = None
            for nid in copied_ids:
                elem = DOC.GetElement(nid)
                if isinstance(elem, DB.WallType):
                    new_type = elem
                    break
            if not new_type:
                for wt in DB.FilteredElementCollector(DOC).OfClass(DB.WallType).ToElements():
                    if wt.Name.upper() == wall_name.upper():
                        new_type = wt
                        break

            # If an old type was replaced, reassign all existing wall instances in project to new master type
            if old_type and new_type:
                all_walls = DB.FilteredElementCollector(DOC).OfClass(DB.Wall).ToElements()
                for w in all_walls:
                    if w.WallType.Id == old_type.Id:
                        w.WallType = new_type
                try:
                    DOC.Delete(old_type.Id)
                except Exception:
                    pass

            t.Commit()
            
            self.TxtStatus.Text = u"Wall Type Loaded: {}".format(wall_name)
            show_alert(u"Wall Type '{}' successfully updated to Master Library version!\n\nAll existing walls in this project were overwritten to the exact Master compound layers, materials, and thicknesses.".format(wall_name), 
                       title=u"Wall Loaded Successfully 👍", is_error=False)
        except Exception as ex:
            if t.HasStarted():
                t.RollBack()
            show_alert(u"Could not copy Wall Type into project:\n{}".format(str(ex)), title=u"Copy Error", is_error=True)
        finally:
            self.Topmost = False
            if need_close:
                try:
                    source_doc.Close(False)
                except:
                    pass

    def on_load_type_only(self, sender, e):
        self.on_load_family(sender, e)

    def on_edit_2025(self, sender, e):
        if not self.selected_family:
            return
        rfa_path = resolve_family_path(self.selected_family)
        if not rfa_path or not os.path.exists(rfa_path):
            show_alert(u"Family file path does not exist on this computer.", title=u"Error", is_error=True)
            return

        if not os.path.exists(REVIT_2025_EXE):
            show_alert(u"Autodesk Revit 2025 was not found at default location:\n{}\nPlease open manually in Revit 2025.".format(REVIT_2025_EXE), title=u"Revit 2025 Not Found", is_warning=True)
            return

        try:
            subprocess.Popen([REVIT_2025_EXE, rfa_path])
            show_alert(u"Launching family directly in Autodesk Revit 2025:\n\n{}\n\nThis ensures company-wide backward compatibility across Revit 2025, 2026, and 2027!".format(os.path.basename(rfa_path)), title=u"Opening in Revit 2025 🛠", is_error=False)
        except Exception as ex:
            show_alert(u"Could not launch Revit 2025:\n{}".format(str(ex)), title=u"Launch Error", is_error=True)

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
            show_alert(u"Catalog refreshed! Total: {} families.".format(len(self.catalog)), title=u"Catalog Refreshed", is_error=False)
        elif res.startswith("4."):
            try:
                subprocess.Popen(["explorer.exe", SHAREPOINT_LIB_ROOT])
            except:
                pass

    def audit_materials_interactive(self):
        if not DOC:
            show_alert(u"No active Revit document open.\nPlease open your Library RVT first.", title=u"Audit Error", is_error=True)
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
            
        show_alert(msg, title=u"Material Audit Results", is_error=False)

    def sync_levels_from_active_doc(self):
        """Reads all Levels from active RVT document and maps all hosted families and Walls to those levels!"""
        if not DOC:
            show_alert(u"No active Revit document open.\nPlease open your Master Library RVT in Revit first.", title=u"Sync Error", is_error=True)
            return

        doc_title = DOC.Title

        levels = DB.FilteredElementCollector(DOC).OfClass(DB.Level).ToElements()
        if not levels:
            show_alert(u"No levels found in active document '{}'.".format(doc_title), title=u"Sync Error", is_warning=True)
            return

        level_name_map = {}
        total_mapped = 0
        wall_types_found = {}

        for lvl in levels:
            lvl_name = lvl.Name.strip()
            clean_lvl_name = "Walls" if lvl_name.upper() == "WALLS" else lvl_name

            # Filter all elements hosted on this level
            lvl_filter = DB.ElementLevelFilter(lvl.Id)
            elements = DB.FilteredElementCollector(DOC).WherePasses(lvl_filter).WhereElementIsNotElementType().ToElements()
            for elem in elements:
                # 1. Standard Loadable Family Instances (Doors, Windows, Columns, Furniture)
                sym = getattr(elem, "Symbol", None)
                if sym and hasattr(sym, "Family"):
                    fam = sym.Family
                    if fam and not fam.IsInPlace:
                        level_name_map[fam.Name.upper()] = clean_lvl_name
                        total_mapped += 1

                # 2. System Wall Instances (Walls placed on WALLS level)
                elif isinstance(elem, DB.Wall) or (hasattr(elem, "WallType") and elem.WallType):
                    w_type = elem.WallType
                    if w_type:
                        try:
                            w_type_name = DB.Element.Name.GetValue(w_type)
                        except:
                            w_type_name = getattr(w_type, "Name", "")
                        if w_type_name and w_type_name not in wall_types_found:
                            thickness_mm = int(round(elem.Width * 304.8)) if hasattr(elem, "Width") and elem.Width else 0
                            kind_str = str(w_type.Kind) if hasattr(w_type, "Kind") else "Basic Wall"
                            wall_types_found[w_type_name] = {
                                "name": w_type_name,
                                "level": clean_lvl_name,
                                "thickness": thickness_mm,
                                "kind": kind_str
                            }

        # Apply to catalog
        updated_count = 0

        # Add or update Walls from the active RVT
        for w_name, w_info in wall_types_found.items():
            existing = next((x for x in self.catalog if x.get("code", "").upper() == w_name.upper()), None)
            if existing:
                existing["category"] = "Walls"
                existing["discipline"] = "ARCHITECTURAL"
                existing["is_level_master"] = True
                existing["is_system_family"] = True
                existing["system_type"] = "Wall"
                existing["source_doc_path"] = DOC.PathName if DOC.PathName else ""
                existing["source_doc_title"] = DOC.Title
                updated_count += 1
            else:
                thick_str = "{} mm".format(w_info["thickness"]) if w_info["thickness"] > 0 else "Standard"
                new_wall = {
                    "code": w_name,
                    "title": w_name,
                    "discipline": "ARCHITECTURAL",
                    "category": "Walls",
                    "types": [w_name],
                    "specs": {
                        "System Family": w_info["kind"],
                        "Category": "Walls",
                        "Thickness": thick_str,
                        "Master File": os.path.basename(DOC.PathName) if DOC.PathName else DOC.Title
                    },
                    "badges": [
                        {"label": "System Wall", "icon": "🧱", "bg": "#B45309"},
                        {"label": "Riyan Standard", "icon": "⭐", "bg": "#15803D"}
                    ],
                    "is_system_family": True,
                    "system_type": "Wall",
                    "is_level_master": True,
                    "source_doc_path": DOC.PathName if DOC.PathName else "",
                    "source_doc_title": DOC.Title,
                    "thumbnail": None
                }
                self.catalog.append(new_wall)
                updated_count += 1

        # Apply level categories & is_level_master to standard families
        for item in self.catalog:
            code = item.get("code", "").upper()
            if code in level_name_map:
                item["category"] = level_name_map[code]
                item["is_level_master"] = True
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
            show_alert(u"Successfully synced {} items (including Walls & level families) directly from active RVT Levels!\nCatalog updated live with Top Priority.".format(updated_count), 
                       title=u"Sync Success 👍", is_error=False)
        except Exception as e:
            show_alert(u"Catalog updated in memory, but error saving to disk:\n{}".format(str(e)), title=u"Save Warning", is_warning=True)

        self.refresh_categories()
        self.apply_filter()

# -------------------------------------------------------------
# Entry Point
# -------------------------------------------------------------
if __name__ == "__main__":
    xaml_file = os.path.join(os.path.dirname(__file__), "ui.xaml")
    win = RiyanFamilyBrowser(xaml_file)
    win.ShowDialog()
