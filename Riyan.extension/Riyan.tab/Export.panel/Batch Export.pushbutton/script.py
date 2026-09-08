# -*- coding: utf-8 -*-
import os
import sys
import json
import traceback

from pyrevit import forms
from pyrevit import script, revit
from Autodesk.Revit import DB
from Autodesk.Revit import UI
import System
from System.Windows import Thickness, GridLength, GridUnitType, HorizontalAlignment, VerticalAlignment, TextWrapping, Window, Application
from System.Windows.Media import SolidColorBrush, ColorConverter
from System.Windows.Controls import StackPanel, Grid, ComboBox, TextBlock, Button, Border, RadioButton, ScrollViewer, Orientation, ProgressBar
from System.Windows.Input import MouseButtonEventHandler
import clr
clr.AddReference('System.Windows.Forms')
import System.Windows.Forms as WinForms

app = __revit__.Application

export_panel_dir = os.path.dirname(os.path.dirname(__file__))
export_mgr_dir = os.path.join(export_panel_dir, 'Export Manager.pushbutton')
import imp
em_script_path = os.path.join(export_mgr_dir, 'script.py')
em_script = imp.load_source('em_script', em_script_path)

from System.Windows.Media.Imaging import BitmapImage, BitmapCacheOption
from System import Uri, UriKind

BRUSH_DONE = SolidColorBrush(ColorConverter.ConvertFromString("#4CAF50"))
BRUSH_EXPORTING = SolidColorBrush(ColorConverter.ConvertFromString("#F59E0B"))
BRUSH_ERROR = SolidColorBrush(ColorConverter.ConvertFromString("#EF4444"))

def get_zoom_fit_type():
    if hasattr(DB, "ZoomType") and hasattr(DB.ZoomType, "FitToPage"):
        return DB.ZoomType.FitToPage
    elif hasattr(DB, "PDFZoomType") and hasattr(DB.PDFZoomType, "FitToPage"):
        return DB.PDFZoomType.FitToPage
    return None

def _safe_get_param_val(p):
    if not p: return ""
    try:
        st = p.StorageType
        if st == DB.StorageType.String:
            return p.AsString() or ""
        elif st == DB.StorageType.Integer:
            return str(p.AsInteger())
        elif st == DB.StorageType.Double:
            try:
                return p.AsValueString() or str(p.AsDouble())
            except Exception:
                return str(p.AsDouble())
        elif st == DB.StorageType.ElementId:
            id_val = p.AsElementId()
            return str(id_val.IntegerValue) if id_val else ""
    except Exception:
        pass
    try:
        return p.AsString() or ""
    except Exception:
        pass
    try:
        return p.AsValueString() or ""
    except Exception:
        pass
    return ""

def log_diag(msg):
    try:
        log_file = os.path.join(os.environ.get("TEMP", "C:\\Temp"), "riyan_batch_debug.log")
        with open(log_file, "a") as f:
            import datetime
            f.write("[{}] {}\n".format(datetime.datetime.now().strftime("%H:%M:%S"), msg))
    except Exception:
        pass

def get_or_open_document(file_path, close_worksets=False):
    """
    Safely gets an already open UI document or opens it fresh in background.
    Returns: (doc, should_close)
    Prevents 'The active document may not be closed from the API' error.
    """
    file_path_abs = os.path.abspath(file_path).lower()
    file_base = os.path.splitext(os.path.basename(file_path))[0].lower()
    
    log_diag("get_or_open_document requested: " + file_path_abs)

    # 0. Check revit.doc directly (Active UI Document)
    try:
        curr_doc = getattr(revit, "doc", None)
        if curr_doc:
            p = getattr(curr_doc, "PathName", "")
            if p and os.path.abspath(p).lower() == file_path_abs:
                log_diag("Found in revit.doc: " + p)
                return (curr_doc, False)
    except Exception as ex:
        log_diag("revit.doc check exception: " + str(ex))

    # 1. Check ActiveUIDocument
    try:
        active_uidoc = getattr(__revit__, "ActiveUIDocument", None)
        if active_uidoc and active_uidoc.Document:
            doc = active_uidoc.Document
            p = getattr(doc, "PathName", "")
            if p and os.path.abspath(p).lower() == file_path_abs:
                log_diag("Found in ActiveUIDocument: " + p)
                return (doc, False)
    except Exception as ex:
        log_diag("ActiveUIDocument check exception: " + str(ex))

    # 2. Check all open documents in Revit UI tabs (exact PathName only)
    # Also PURGE any orphaned detached documents left in memory from previous sessions
    for d in list(app.Documents):
        try:
            p = getattr(d, 'PathName', '')
            if p and os.path.abspath(p).lower() == file_path_abs:
                log_diag("Found in app.Documents (open tab): " + p)
                return (d, False)
            if not p:
                # Detached background document left in memory from a previous run
                t = getattr(d, 'Title', '').strip().lower()
                if t == file_base or t == (file_base + "_detached") or (file_base in t and "detached" in t):
                    log_diag("Purging orphaned detached document from memory: " + t)
                    try:
                        d.Close(False)
                    except Exception as cex:
                        log_diag("Could not close orphan: " + str(cex))
        except Exception as ex:
            log_diag("app.Documents loop exception: " + str(ex))

    # 3. Background open fresh from disk
    log_diag("Opening fresh background document from disk with all worksets...")
    opt = DB.OpenOptions()
    opt.DetachFromCentralOption = DB.DetachFromCentralOption.DetachAndPreserveWorksets
    
    # ALWAYS Open ALL Worksets (closing worksets deletes them permanently in detached mode!)
    ws_opt = DB.WorksetConfiguration(DB.WorksetConfigurationOption.OpenAllWorksets)
    opt.SetOpenWorksetsConfiguration(ws_opt)

    model_path = DB.ModelPathUtils.ConvertUserVisiblePathToModelPath(file_path)
    bg_doc = app.OpenDocumentFile(model_path, opt)
    
    # Diagnostic audit of model elements
    try:
        w_cnt = DB.FilteredElementCollector(bg_doc).OfCategory(DB.BuiltInCategory.OST_Walls).GetElementCount()
        d_cnt = DB.FilteredElementCollector(bg_doc).OfCategory(DB.BuiltInCategory.OST_Doors).GetElementCount()
        ws_col = DB.FilteredWorksetCollector(bg_doc).OfKind(DB.WorksetKind.UserWorkset).ToWorksets()
        log_diag("Opened bg_doc successfully! Title='{}', Walls={}, Doors={}, UserWorksets={}".format(
            getattr(bg_doc, 'Title', '-'), w_cnt, d_cnt, ws_col.Count))
    except Exception as ex:
        log_diag("Audit exception: " + str(ex))

    # Reload Revit links if any
    try:
        link_types = DB.FilteredElementCollector(bg_doc).OfClass(DB.RevitLinkType).ToElements()
        for lt in link_types:
            try:
                if not DB.RevitLinkType.IsLoaded(bg_doc, lt.Id):
                    log_diag("Reloading link: " + str(lt.Name))
                    lt.Reload()
            except Exception as lex:
                log_diag("Link reload note: " + str(lex))
    except Exception as ex:
        log_diag("Link collector exception: " + str(ex))

    return (bg_doc, True)

# ----------------- MOCK CLASSES -----------------
class MockParameter:
    def __init__(self, name, val):
        self._name = name
        self._val = val
    def AsValueString(self): return self._val
    def AsString(self): return self._val
    @property
    def Definition(self):
        class Def: pass
        d = Def()
        d.Name = self._name
        return d

class MockElement:
    def __init__(self, name, number, unique_id):
        self.Name = name
        self.SheetNumber = number
        self.UniqueId = unique_id
        self.sheet_collection = ""
        self.Parameters = []
        self._param_dict = {}
        if number:
            self.add_param("Sheet Number", number)
            self.add_param("Sheet_Number", number)
            self.add_param("Drawing Number", number)
        if name:
            self.add_param("Sheet Name", name)
            self.add_param("Name", name)

    def add_param(self, name, val):
        if not name: return
        p = MockParameter(name, val)
        self.Parameters.append(p)
        self._param_dict[name] = p
        self._param_dict[name.strip().lower()] = p

    def LookupParameter(self, name):
        if not name: return None
        p = self._param_dict.get(name, None)
        if not p:
            p = self._param_dict.get(name.strip().lower(), None)
        return p

class MockDoc:
    def __init__(self):
        self.ProjectInformation = MockElement("ProjInfo", "", "")

class MockQueueItem:
    def __init__(self, sheet, target_filename, ui_row=None):
        self.SheetId = sheet.UniqueId
        self.SheetNumber = getattr(sheet, 'SheetNumber', '')
        self.SheetName = getattr(sheet, 'Name', '')
        self.TargetFileName = target_filename
        self.ui_row = ui_row
        self._status = ""
        
        class MockSheetVM:
            def __init__(self, s):
                self.Sheet = s
        self.SheetVM = MockSheetVM(sheet)
        
    @property
    def Status(self): return self._status
    @Status.setter
    def Status(self, value):
        self._status = value
        if self.ui_row:
            try:
                if value == "Exporting...":
                    self.ui_row.set_status("Exporting...", is_exporting=True)
                elif value == "Done":
                    self.ui_row.set_status("Done", is_done=True)
                elif value == "Error":
                    self.ui_row.set_status("Error", is_error=True)
                elif value == "Pending":
                    self.ui_row.set_status("Pending")
                elif value == "Skipped":
                    self.ui_row.set_status("Skipped")
                elif value:
                    self.ui_row.set_status(value)
            except Exception:
                pass

# ----------------- UI CLASSES -----------------
class SheetRow:
    def __init__(self, mock_sheet, parent_file_row, form_instance, parent_group=None):
        self.mock_sheet = mock_sheet
        self.parent = parent_file_row
        self.parent_group = parent_group
        self.form = form_instance
        self.generated_name = ""
        self._updating = False
        
        brush_main = form_instance.FindResource("TextMain")
        brush_dim = form_instance.FindResource("TextDim")
        
        self.border = Border()
        self.border.BorderThickness = Thickness(0,0,0,1)
        self.border.BorderBrush = form_instance.FindResource("BorderColor")
        self.border.Padding = Thickness(20, 2, 5, 2)
        self.border.Background = SolidColorBrush(System.Windows.Media.Colors.Transparent)
        self.border.Cursor = System.Windows.Input.Cursors.Hand
        
        self.grid = Grid()
        self.border.Child = self.grid
        
        from System.Windows.Data import Binding, BindingMode
        for i in range(9):
            cd = System.Windows.Controls.ColumnDefinition()
            if i % 2 == 0:
                col_index = i // 2
                try:
                    h_col = form_instance.FindName("HCol" + str(col_index))
                    if h_col:
                        b = Binding("Width")
                        b.Source = h_col
                        b.Mode = BindingMode.TwoWay
                        System.Windows.Data.BindingOperations.SetBinding(cd, System.Windows.Controls.ColumnDefinition.WidthProperty, b)
                    else:
                        raise Exception("Not found")
                except:
                    fixed_widths = {0: 330, 1: 140, 2: 140, 3: 160, 4: 180}
                    if col_index in fixed_widths:
                        cd.Width = GridLength(fixed_widths[col_index], GridUnitType.Pixel)
                        cd.SharedSizeGroup = "Col" + str(col_index)
            else:
                cd.Width = GridLength(3, GridUnitType.Pixel)
            self.grid.ColumnDefinitions.Add(cd)
            
        sp_name = StackPanel()
        sp_name.Orientation = Orientation.Horizontal
        
        self.chk = System.Windows.Controls.CheckBox()
        self.chk.IsChecked = False
        self.chk.VerticalAlignment = VerticalAlignment.Center
        self.chk.Margin = Thickness(38, 0, 5, 0) if parent_group else Thickness(30, 0, 5, 0)
        self.chk.Click += self.on_chk_clicked
        sp_name.Children.Add(self.chk)
        
        self.txt_name = TextBlock()
        self.txt_name.Text = self.mock_sheet.SheetNumber + " - " + self.mock_sheet.Name
        self.txt_name.ToolTip = self.mock_sheet.SheetNumber + " - " + self.mock_sheet.Name
        self.txt_name.TextTrimming = System.Windows.TextTrimming.CharacterEllipsis
        sp_name.ClipToBounds = True
        self.txt_name.VerticalAlignment = VerticalAlignment.Center
        if brush_main: self.txt_name.Foreground = brush_main
        sp_name.Children.Add(self.txt_name)
        
        Grid.SetColumn(sp_name, 0)
        self.grid.Children.Add(sp_name)
        
        self.txt_status = TextBlock()
        self.txt_status.Text = ""
        self.txt_status.VerticalAlignment = VerticalAlignment.Center
        self.txt_status.HorizontalAlignment = HorizontalAlignment.Center
        self.txt_status.TextAlignment = System.Windows.TextAlignment.Center
        self.txt_status.Margin = Thickness(5, 0, 5, 0)
        self.txt_status.TextTrimming = System.Windows.TextTrimming.CharacterEllipsis
        if brush_main: self.txt_status.Foreground = brush_dim
        Grid.SetColumn(self.txt_status, 8)
        self.grid.Children.Add(self.txt_status)
        
        self.border.MouseLeftButtonDown += self.on_select

    def on_chk_clicked(self, sender, e):
        if self.parent_group:
            self.parent_group.update_collection_checkbox()
        elif self.parent:
            self.parent.update_master_checkbox()

    def on_select(self, sender, e):
        self.form.select_sheet(self)
        
    def set_status(self, msg, is_done=False, is_exporting=False, is_error=False):
        clean_msg = msg
        for tag in ["[Done] ", "[Exporting] ", "[Error] "]:
            if clean_msg.startswith(tag):
                clean_msg = clean_msg[len(tag):]
                
        if is_done:
            self.txt_status.Text = clean_msg
            self.txt_status.Foreground = BRUSH_DONE
        elif is_exporting:
            self.txt_status.Text = clean_msg
            self.txt_status.Foreground = BRUSH_EXPORTING
            try:
                self.border.BringIntoView()
            except:
                pass
        elif is_error:
            self.txt_status.Text = clean_msg
            self.txt_status.Foreground = BRUSH_ERROR
        else:
            self.txt_status.Text = clean_msg
            brush_dim = self.form.FindResource("TextDim")
            if brush_dim: self.txt_status.Foreground = brush_dim
        self.txt_status.ToolTip = clean_msg
        self.form.do_events()

class CollectionGroup:
    def __init__(self, collection_name, parent_file_row, form_instance):
        self.collection_name = collection_name
        self.parent = parent_file_row
        self.form = form_instance
        self.sheet_rows = []
        self.is_expanded = True
        self._updating_checks = False
        
        brush_main = form_instance.FindResource("TextMain")
        brush_dim = form_instance.FindResource("TextDim")
        border_brush = form_instance.FindResource("BorderColor")
        header_bg = form_instance.FindResource("TitleBarBg")
        
        self.container = StackPanel()
        self.container.Orientation = Orientation.Vertical
        
        self.header_border = Border()
        self.header_border.BorderThickness = Thickness(0, 0, 0, 1)
        if border_brush: self.header_border.BorderBrush = border_brush
        if header_bg: self.header_border.Background = header_bg
        else: self.header_border.Background = SolidColorBrush(System.Windows.Media.Colors.Transparent)
        self.header_border.Padding = Thickness(5, 4, 5, 4)
        self.header_border.Cursor = System.Windows.Input.Cursors.Hand
        self.header_border.MouseLeftButtonDown += self.on_header_click
        
        self.grid = Grid()
        self.header_border.Child = self.grid
        
        from System.Windows.Data import Binding, BindingMode
        for i in range(9):
            cd = System.Windows.Controls.ColumnDefinition()
            if i % 2 == 0:
                col_index = i // 2
                try:
                    h_col = form_instance.FindName("HCol" + str(col_index))
                    if h_col:
                        b = Binding("Width")
                        b.Source = h_col
                        b.Mode = BindingMode.TwoWay
                        System.Windows.Data.BindingOperations.SetBinding(cd, System.Windows.Controls.ColumnDefinition.WidthProperty, b)
                    else:
                        raise Exception("Not found")
                except:
                    fixed_widths = {0: 330, 1: 140, 2: 140, 3: 160, 4: 180}
                    if col_index in fixed_widths:
                        cd.Width = GridLength(fixed_widths[col_index], GridUnitType.Pixel)
                        cd.SharedSizeGroup = "Col" + str(col_index)
            else:
                cd.Width = GridLength(3, GridUnitType.Pixel)
            self.grid.ColumnDefinitions.Add(cd)
            
        sp = StackPanel()
        sp.Orientation = Orientation.Horizontal
        sp.VerticalAlignment = VerticalAlignment.Center
        
        self.chk = System.Windows.Controls.CheckBox()
        self.chk.IsChecked = False
        self.chk.IsThreeState = True
        self.chk.VerticalAlignment = VerticalAlignment.Center
        self.chk.Margin = Thickness(18, 0, 5, 0)
        self.chk.Click += self.on_chk_clicked
        sp.Children.Add(self.chk)
        
        self.btn_expand = Button()
        self.btn_expand.Content = "-"
        self.btn_expand.Width = 20
        self.btn_expand.Height = 20
        self.btn_expand.Background = SolidColorBrush(System.Windows.Media.Colors.Transparent)
        self.btn_expand.BorderThickness = Thickness(0)
        if brush_dim: self.btn_expand.Foreground = brush_dim
        self.btn_expand.Cursor = System.Windows.Input.Cursors.Hand
        self.btn_expand.Click += self.on_expand
        sp.Children.Add(self.btn_expand)
        
        self.txt_title = TextBlock()
        self.txt_title.Text = self.collection_name
        self.txt_title.FontWeight = System.Windows.FontWeights.SemiBold
        self.txt_title.VerticalAlignment = VerticalAlignment.Center
        self.txt_title.Margin = Thickness(5, 0, 5, 0)
        if brush_main: self.txt_title.Foreground = brush_main
        sp.Children.Add(self.txt_title)
        
        Grid.SetColumn(sp, 0)
        self.grid.Children.Add(sp)
        
        self.container.Children.Add(self.header_border)
        
        self.child_stack = StackPanel()
        self.child_stack.Orientation = Orientation.Vertical
        self.container.Children.Add(self.child_stack)

    def on_header_click(self, sender, e):
        if e.OriginalSource == self.chk or e.OriginalSource == self.btn_expand:
            return
        self.on_expand(sender, e)

    def on_expand(self, sender, e):
        self.is_expanded = not self.is_expanded
        self.btn_expand.Content = "-" if self.is_expanded else "+"
        self.child_stack.Visibility = System.Windows.Visibility.Visible if self.is_expanded else System.Windows.Visibility.Collapsed

    def on_chk_clicked(self, sender, e):
        val = (self.chk.IsChecked == True)
        self.chk.IsChecked = val
        for sr in self.sheet_rows:
            sr.chk.IsChecked = val
        self.parent.update_master_checkbox()

    def update_collection_checkbox(self):
        checked = sum(1 for sr in self.sheet_rows if sr.chk.IsChecked == True)
        total = len(self.sheet_rows)
        if total > 0 and checked == total:
            self.chk.IsChecked = True
        elif checked == 0:
            self.chk.IsChecked = False
        else:
            self.chk.IsChecked = None
        self.parent.update_master_checkbox()

    def add_sheet_row(self, s_row):
        self.sheet_rows.append(s_row)
        self.child_stack.Children.Add(s_row.border)
        count = len(self.sheet_rows)
        self.txt_title.Text = "{} ({} sheet{})".format(self.collection_name, count, "s" if count != 1 else "")

    def set_checked_state(self, is_checked):
        self.chk.IsChecked = is_checked
        for sr in self.sheet_rows:
            sr.chk.IsChecked = is_checked

class FileRow:
    def __init__(self, file_path, form_instance):
        self.file_path = file_path
        self.form = form_instance
        self.profiles = form_instance.profiles
        self.output_location = ""
        self.mock_doc = MockDoc()
        self.sets_dict = {}
        self.sheet_rows = []
        self.collection_groups = []
        self.is_expanded = True
        self._updating_master = False
        
        brush_main = form_instance.FindResource("TextMain")
        brush_dim = form_instance.FindResource("TextDim")
        btn_style = form_instance.FindResource("SecondaryBtn")
        
        self.main_container = StackPanel()
        
        self.grid = Grid()
        self.grid.Margin = Thickness(0, 0, 0, 0)
        self.main_container.Children.Add(self.grid)
        
        from System.Windows.Data import Binding, BindingMode
        for i in range(9):
            cd = System.Windows.Controls.ColumnDefinition()
            if i % 2 == 0:
                col_index = i // 2
                try:
                    h_col = form_instance.FindName("HCol" + str(col_index))
                    if h_col:
                        b = Binding("Width")
                        b.Source = h_col
                        b.Mode = BindingMode.TwoWay
                        System.Windows.Data.BindingOperations.SetBinding(cd, System.Windows.Controls.ColumnDefinition.WidthProperty, b)
                    else:
                        raise Exception("Not found")
                except:
                    # Fallback if binding fails
                    fixed_widths = {0: 330, 1: 140, 2: 140, 3: 160, 4: 180} # 4 is * in XAML but we give it a min fallback
                    if col_index in fixed_widths:
                        cd.Width = GridLength(fixed_widths[col_index], GridUnitType.Pixel)
                        cd.SharedSizeGroup = "Col" + str(col_index)
            else:
                cd.Width = GridLength(3, GridUnitType.Pixel)
            self.grid.ColumnDefinitions.Add(cd)
            
        sp_file = StackPanel()
        sp_file.Orientation = Orientation.Horizontal
        sp_file.VerticalAlignment = VerticalAlignment.Center
        
        self.chk_all = System.Windows.Controls.CheckBox()
        self.chk_all.IsChecked = False
        self.chk_all.IsThreeState = True
        self.chk_all.VerticalAlignment = VerticalAlignment.Center
        self.chk_all.Margin = Thickness(5, 0, 5, 0)
        self.chk_all.Click += self.on_chk_all_clicked
        sp_file.Children.Add(self.chk_all)
        
        self.btn_expand = Button()
        self.btn_expand.Content = "-"
        self.btn_expand.Width = 20
        self.btn_expand.Height = 20
        self.btn_expand.Background = SolidColorBrush(System.Windows.Media.Colors.Transparent)
        self.btn_expand.BorderThickness = Thickness(0)
        self.btn_expand.Foreground = brush_main if brush_main else SolidColorBrush(System.Windows.Media.Colors.White)
        self.btn_expand.Click += self.on_expand
        sp_file.Children.Add(self.btn_expand)
        
        self.txt_file = TextBlock()
        self.txt_file.Text = os.path.basename(self.file_path)
        self.txt_file.ToolTip = self.file_path
        self.txt_file.FontWeight = System.Windows.FontWeights.SemiBold
        self.txt_file.TextTrimming = System.Windows.TextTrimming.CharacterEllipsis
        sp_file.ClipToBounds = True
        self.txt_file.VerticalAlignment = VerticalAlignment.Center
        if brush_main: self.txt_file.Foreground = brush_main
        sp_file.Children.Add(self.txt_file)
        
        Grid.SetColumn(sp_file, 0)
        self.grid.Children.Add(sp_file)
        
        self.cmb_set = ComboBox()
        self.cmb_set.VerticalAlignment = VerticalAlignment.Center
        self.cmb_set.Margin = Thickness(5,0,5,0)
        self.cmb_set.SelectionChanged += self.on_options_changed
        Grid.SetColumn(self.cmb_set, 2)
        self.grid.Children.Add(self.cmb_set)
        
        self.cmb_profile = ComboBox()
        self.cmb_profile.ItemsSource = form_instance.profiles
        self.cmb_profile.VerticalAlignment = VerticalAlignment.Center
        self.cmb_profile.Margin = Thickness(5,0,5,0)
        if form_instance.profiles:
            self.cmb_profile.SelectedIndex = 0
        self.cmb_profile.SelectionChanged += self.on_options_changed
        Grid.SetColumn(self.cmb_profile, 4)
        self.grid.Children.Add(self.cmb_profile)
        
        loc_grid = Grid()
        loc_grid.ColumnDefinitions.Add(System.Windows.Controls.ColumnDefinition())
        cd_btn = System.Windows.Controls.ColumnDefinition()
        cd_btn.Width = GridLength(35, GridUnitType.Pixel)
        loc_grid.ColumnDefinitions.Add(cd_btn)
        
        self.txt_loc = TextBlock()
        self.txt_loc.Text = "Select Folder..."
        self.txt_loc.VerticalAlignment = VerticalAlignment.Center
        if brush_dim: self.txt_loc.Foreground = brush_dim
        Grid.SetColumn(self.txt_loc, 0)
        loc_grid.Children.Add(self.txt_loc)
        
        self.btn_browse = Button()
        self.btn_browse.Content = "..."
        if btn_style: self.btn_browse.Style = btn_style
        self.btn_browse.Height = 24
        self.btn_browse.Click += self.on_browse
        Grid.SetColumn(self.btn_browse, 1)
        loc_grid.Children.Add(self.btn_browse)
        
        Grid.SetColumn(loc_grid, 6)
        loc_grid.Margin = Thickness(5,0,5,0)
        self.grid.Children.Add(loc_grid)
        
        self.txt_status = TextBlock()
        self.txt_status.Text = ""
        self.txt_status.VerticalAlignment = VerticalAlignment.Center
        self.txt_status.HorizontalAlignment = HorizontalAlignment.Center
        self.txt_status.TextAlignment = System.Windows.TextAlignment.Center
        self.txt_status.Margin = Thickness(5, 0, 5, 0)
        self.txt_status.TextTrimming = System.Windows.TextTrimming.CharacterEllipsis
        if brush_main: self.txt_status.Foreground = brush_main
        Grid.SetColumn(self.txt_status, 8)
        self.grid.Children.Add(self.txt_status)
        
        self.sheet_stack = StackPanel()
        self.main_container.Children.Add(self.sheet_stack)

    def on_chk_all_clicked(self, sender, e):
        val = (self.chk_all.IsChecked == True)
        self.chk_all.IsChecked = val
        for cg in getattr(self, 'collection_groups', []):
            cg.set_checked_state(val)
        for sr in self.sheet_rows:
            sr.chk.IsChecked = val

    def update_master_checkbox(self):
        checked = sum(1 for sr in self.sheet_rows if sr.chk.IsChecked == True)
        total = len(self.sheet_rows)
        if total > 0 and checked == total:
            self.chk_all.IsChecked = True
        elif checked == 0:
            self.chk_all.IsChecked = False
        else:
            self.chk_all.IsChecked = None

    def on_expand(self, sender, e):
        self.is_expanded = not self.is_expanded
        self.btn_expand.Content = "-" if self.is_expanded else "+"
        self.sheet_stack.Visibility = System.Windows.Visibility.Visible if self.is_expanded else System.Windows.Visibility.Collapsed

    def on_browse(self, sender, e):
        dlg = WinForms.FolderBrowserDialog()
        if dlg.ShowDialog() == WinForms.DialogResult.OK:
            self.output_location = dlg.SelectedPath
            self.txt_loc.Text = os.path.basename(dlg.SelectedPath)
            
    def set_status(self, msg, is_done=False, is_exporting=False, is_error=False):
        clean_msg = msg
        for tag in ["[Done] ", "[Exporting] ", "[Error] "]:
            if clean_msg.startswith(tag):
                clean_msg = clean_msg[len(tag):]
                
        if is_done:
            self.txt_status.Text = "[Done] " + clean_msg
            self.txt_status.Foreground = BRUSH_DONE
        elif is_exporting:
            self.txt_status.Text = "[Exporting] " + clean_msg
            self.txt_status.Foreground = BRUSH_EXPORTING
        elif is_error:
            self.txt_status.Text = "[Error] " + clean_msg
            self.txt_status.Foreground = BRUSH_ERROR
        else:
            self.txt_status.Text = clean_msg
            brush_dim = self.form.FindResource("TextDim")
            if brush_dim: self.txt_status.Foreground = brush_dim
        self.txt_status.ToolTip = self.txt_status.Text
        self.form.do_events()
        
    def on_options_changed(self, sender, e):
        try:
            if not self.cmb_set.SelectedItem or not self.cmb_profile.SelectedItem:
                return
                
            set_name = self.cmb_set.SelectedItem
            profile_name = self.cmb_profile.SelectedItem
            scheme_parts = self.form.settings.get("schemes", {}).get(profile_name, [])
            if not scheme_parts:
                scheme_parts = self.form.settings.get("combined_schemes", {}).get(profile_name, [])
            
            self.sheet_stack.Children.Clear()
            self.sheet_rows = []
            self.collection_groups = []
            
            mock_sheets = self.sets_dict.get(set_name, [])
            has_collections = any(bool(getattr(ms, 'sheet_collection', '')) for ms in mock_sheets)
            
            if not has_collections:
                for ms in mock_sheets:
                    s_row = SheetRow(ms, self, self.form)
                    name = em_script.generate_filename(ms, scheme_parts, self.mock_doc)
                    s_row.generated_name = name
                    s_row.txt_name.Text = name
                    s_row.txt_name.ToolTip = name
                    self.sheet_rows.append(s_row)
                    self.sheet_stack.Children.Add(s_row.border)
            else:
                coll_map = {}
                for ms in mock_sheets:
                    c = getattr(ms, 'sheet_collection', '')
                    if not c:
                        c = "Other Sheets"
                    if c not in coll_map:
                        coll_map[c] = []
                    coll_map[c].append(ms)
                
                sorted_colls = sorted([c for c in coll_map.keys() if c != "Other Sheets"])
                if "Other Sheets" in coll_map:
                    sorted_colls.append("Other Sheets")
                    
                for c_name in sorted_colls:
                    c_group = CollectionGroup(c_name, self, self.form)
                    self.collection_groups.append(c_group)
                    self.sheet_stack.Children.Add(c_group.container)
                    
                    for ms in coll_map[c_name]:
                        s_row = SheetRow(ms, self, self.form, parent_group=c_group)
                        name = em_script.generate_filename(ms, scheme_parts, self.mock_doc)
                        s_row.generated_name = name
                        s_row.txt_name.Text = name
                        s_row.txt_name.ToolTip = name
                        self.sheet_rows.append(s_row)
                        c_group.add_sheet_row(s_row)
                        
            self.update_master_checkbox()
        except Exception as ex:
            import traceback
            forms.alert(str(ex) + '\n\n' + traceback.format_exc(), title='Options Error')

class BatchExportForm(forms.WPFWindow):
    def __init__(self, xaml_file_name):
        forms.WPFWindow.__init__(self, xaml_file_name)
        self.rows = []
        self._cancel_export = False
        self.selected_sheet = None
        self.preview_cache = {}
        
        self.settings = {}
        settings_path = os.path.join(export_mgr_dir, "naming_settings.json")
        if os.path.exists(settings_path):
            with open(settings_path, 'r') as f:
                self.settings = json.load(f)
        all_schemes = set(self.settings.get("schemes", {}).keys())
        all_schemes.update(self.settings.get("combined_schemes", {}).keys())
        self.profiles = sorted(list(all_schemes))

        if hasattr(self, 'ImgPreview') and self.ImgPreview:
            self.ImgPreview.MouseLeftButtonDown += self.on_preview_image_click

        self.doc_cache = {}
        class DummyQueue:
            class DummyItems:
                def Refresh(self): pass
            Items = DummyItems()
        self.GridQueue = DummyQueue()
        try:
            self.Closed += self.on_window_closed
        except Exception:
            pass

    def get_cached_document(self, file_path):
        key = os.path.abspath(file_path).lower()
        if key in self.doc_cache:
            d, should_close = self.doc_cache[key]
            if d and getattr(d, 'IsValidObject', True):
                return (d, False)
        doc, should_close = get_or_open_document(file_path, close_worksets=False)
        self.doc_cache[key] = (doc, should_close)
        return (doc, False)

    def cleanup_cached_documents(self):
        for key, (d, should_close) in self.doc_cache.items():
            if should_close and d:
                try:
                    if getattr(d, 'IsValidObject', True):
                        d.Close(False)
                except Exception:
                    pass
        self.doc_cache.clear()

    def on_window_closed(self, sender, e):
        self.cleanup_cached_documents()
        
    def do_events(self):
        Application.Current.Dispatcher.Invoke(System.Windows.Threading.DispatcherPriority.Background, System.Action(lambda: None))

    def TitleBar_MouseDown(self, sender, e):
        try:
            self.DragMove()
        except:
            pass

    def CloseBtn_Click(self, sender, e):
        self._cancel_export = True
        self.cleanup_cached_documents()
        self.Close()

    def MinimizeBtn_Click(self, sender, e):
        self.WindowState = System.Windows.WindowState.Minimized

    def BtnTheme_Click(self, sender, e):
        current = self.settings.get("theme", "Dark")
        new_theme = "Light" if current == "Dark" else "Dark"
        self.settings["theme"] = new_theme
        
        try:
            settings_path = os.path.join(export_mgr_dir, "naming_settings.json")
            with open(settings_path, 'w') as f:
                json.dump(self.settings, f, indent=4)
            forms.alert("Theme changed to {}. Please close and reopen.".format(new_theme), title="Theme Switched")
        except Exception as ex:
            forms.alert("Error saving theme: " + str(ex))

    def select_sheet(self, sheet_row):
        brush_main = self.FindResource("TextMain")
        brush_dim = self.FindResource("TextDim")
        
        if self.selected_sheet:
            self.selected_sheet.border.Background = SolidColorBrush(System.Windows.Media.Colors.Transparent)
            if brush_main: self.selected_sheet.txt_name.Foreground = brush_main
            if brush_dim: self.selected_sheet.txt_status.Foreground = brush_dim
            
        self.selected_sheet = sheet_row
        select_color = ColorConverter.ConvertFromString("#FFF2C8")
        self.selected_sheet.border.Background = SolidColorBrush(select_color)
        
        black_brush = SolidColorBrush(System.Windows.Media.Colors.Black)
        self.selected_sheet.txt_name.Foreground = black_brush
        self.selected_sheet.txt_status.Foreground = black_brush

        # Update Right Side Panel (Sheet Info & Preview)
        try:
            ms = sheet_row.mock_sheet
            if hasattr(self, 'TxtDetailNumber'):
                self.TxtDetailNumber.Text = getattr(ms, 'SheetNumber', '-')
            if hasattr(self, 'TxtDetailName'):
                self.TxtDetailName.Text = getattr(ms, 'Name', '-')
            if hasattr(self, 'TxtDetailCollection'):
                self.TxtDetailCollection.Text = getattr(ms, 'sheet_collection', '') or 'None'
            if hasattr(self, 'TxtDetailExportName'):
                self.TxtDetailExportName.Text = sheet_row.generated_name or '-'
            if hasattr(self, 'TxtDetailModel'):
                self.TxtDetailModel.Text = os.path.basename(sheet_row.parent.file_path)

            # Check cached preview
            model_path = os.path.abspath(sheet_row.parent.file_path).lower()
            sheet_id = ms.UniqueId
            cache_key = (model_path, sheet_id)
            
            # Immediately clear and hide previous image so no stale preview ever lingers
            if hasattr(self, 'ImgPreview') and self.ImgPreview:
                self.ImgPreview.Source = None
                self.ImgPreview.Visibility = System.Windows.Visibility.Collapsed

            if cache_key in self.preview_cache and os.path.exists(self.preview_cache[cache_key]):
                self.display_preview_image(self.preview_cache[cache_key])
            else:
                if hasattr(self, 'GridPreviewLoading'):
                    self.GridPreviewLoading.Visibility = System.Windows.Visibility.Collapsed
                if hasattr(self, 'GridPreviewPrompt'):
                    self.GridPreviewPrompt.Visibility = System.Windows.Visibility.Visible
                if hasattr(self, 'TxtPreviewHint'):
                    self.TxtPreviewHint.Text = "Click Preview to view"
                if hasattr(self, 'BtnDoPreview'):
                    self.BtnDoPreview.Visibility = System.Windows.Visibility.Visible
        except Exception:
            pass

    def display_preview_image(self, img_path):
        try:
            bi = BitmapImage()
            bi.BeginInit()
            bi.CacheOption = BitmapCacheOption.OnLoad
            bi.UriSource = Uri(img_path, UriKind.Absolute)
            bi.EndInit()
            bi.Freeze()
            self.ImgPreview.Source = bi
            self.ImgPreview.Visibility = System.Windows.Visibility.Visible
        except Exception as ex:
            forms.alert("Error loading preview image: " + str(ex))
        finally:
            if hasattr(self, 'GridPreviewPrompt'):
                self.GridPreviewPrompt.Visibility = System.Windows.Visibility.Collapsed
            if hasattr(self, 'BtnDoPreview'):
                self.BtnDoPreview.Visibility = System.Windows.Visibility.Collapsed
            if hasattr(self, 'GridPreviewLoading'):
                self.GridPreviewLoading.Visibility = System.Windows.Visibility.Collapsed

    def on_preview_image_click(self, sender, e):
        if self.selected_sheet:
            model_path = os.path.abspath(self.selected_sheet.parent.file_path).lower()
            sheet_id = self.selected_sheet.mock_sheet.UniqueId
            cache_key = (model_path, sheet_id)
            if cache_key in self.preview_cache:
                img_path = self.preview_cache[cache_key]
                if os.path.exists(img_path):
                    from _preview_script import show_preview
                    title = self.selected_sheet.generated_name or (self.selected_sheet.mock_sheet.SheetNumber + " - " + self.selected_sheet.mock_sheet.Name)
                    show_preview(img_path, title)

    def BtnPreview_Click(self, sender, e):
        if not self.selected_sheet:
            forms.alert("Please select a sheet from the list first.", title="No Sheet Selected")
            return
            
        sr = self.selected_sheet
        file_path = sr.parent.file_path
        file_path_abs = os.path.abspath(file_path).lower()
        sheet_id = sr.mock_sheet.UniqueId
        cache_key = (file_path_abs, sheet_id)
        
        if hasattr(self, 'BtnDoPreview'):
            self.BtnDoPreview.IsEnabled = False

        sr.set_status("Loading Vector Preview...")
        if hasattr(self, 'GridPreviewLoading'):
            self.GridPreviewLoading.Visibility = System.Windows.Visibility.Visible
        if hasattr(self, 'GridPreviewPrompt'):
            self.GridPreviewPrompt.Visibility = System.Windows.Visibility.Collapsed
        if hasattr(self, 'ImgPreview'):
            self.ImgPreview.Visibility = System.Windows.Visibility.Collapsed
        self.do_events()
        
        bg_doc = None
        try:
            bg_doc, _ = self.get_cached_document(file_path)
            
            sheet_element = bg_doc.GetElement(sheet_id)
            if not sheet_element:
                forms.alert("Sheet not found in document.")
                sr.set_status("")
                return

            import zlib
            import re
            model_hash = hex(zlib.crc32(file_path_abs.encode('utf-8')) & 0xffffffff)[2:]
            model_clean = re.sub(r'[^a-zA-Z0-9_]', '', os.path.splitext(os.path.basename(file_path))[0])[:15]
            temp_dir = os.environ.get("TEMP")
            pdf_prefix = "riyan_prev_{}_{}_{}".format(model_clean, model_hash, sheet_element.UniqueId)
            png_out = os.path.join(temp_dir, pdf_prefix + ".png")

            # 1. Clean up old temp preview files for this exact model and sheet
            try:
                for f in os.listdir(temp_dir):
                    if f.startswith(pdf_prefix):
                        try: os.remove(os.path.join(temp_dir, f))
                        except: pass
            except Exception:
                pass

            # 2. Export 1-sheet PDF for preview
            pdf_opt = DB.PDFExportOptions()
            pdf_opt.FileName = pdf_prefix
            pdf_opt.Combine = True
            
            # Check if sheet contains 3D views or shaded elements requiring raster processing
            needs_raster = False
            try:
                for vpid in sheet_element.GetAllViewports():
                    vp = bg_doc.GetElement(vpid)
                    if not vp: continue
                    v = bg_doc.GetElement(vp.ViewId)
                    if not v: continue
                    if isinstance(v, DB.View3D) or getattr(v, "ViewType", None) == DB.ViewType.ThreeD:
                        needs_raster = True
                        break
                    ds = str(getattr(v, "DisplayStyle", ""))
                    if any(s in ds for s in ["Shading", "Realistic", "ConsistentColors", "Textures"]):
                        needs_raster = True
                        break
                    if getattr(v, "AreShadowsOn", False) or getattr(v, "AmbientShadows", False):
                        needs_raster = True
                        break
            except Exception:
                pass

            # Only use raster if view specifically requires it (3D or shaded).
            # Standard 2D plans and sections use native Vector export for 100% CAD precision.
            if hasattr(pdf_opt, "AlwaysUseRaster") and needs_raster:
                pdf_opt.AlwaysUseRaster = True

            if hasattr(DB, "RasterQualityType"):
                pdf_opt.RasterQuality = DB.RasterQualityType.High if needs_raster else DB.RasterQualityType.Medium

            if hasattr(DB, "ColorDepthType") and hasattr(pdf_opt, "ColorDepth"):
                pdf_opt.ColorDepth = DB.ColorDepthType.Color

            zt = get_zoom_fit_type()
            if zt is not None:
                pdf_opt.ZoomType = zt

            try:
                bg_doc.Regenerate()
            except Exception:
                pass

            log_diag("Exporting preview for Sheet: {} - {}, needs_raster={}".format(
                getattr(sheet_element, 'SheetNumber', '-'), getattr(sheet_element, 'Name', '-'), needs_raster))

            views = System.Collections.Generic.List[DB.ElementId]()
            views.Add(sheet_element.Id)
            
            export_ok = bg_doc.Export(temp_dir, views, pdf_opt)

            # Locate the exported PDF file
            actual_pdf = os.path.join(temp_dir, pdf_prefix + ".pdf")
            if not os.path.exists(actual_pdf):
                actual_pdf = None
                try:
                    for f in os.listdir(temp_dir):
                        if f.endswith(".pdf") and f.startswith(pdf_prefix):
                            actual_pdf = os.path.join(temp_dir, f)
                            break
                except Exception:
                    pass

            if not actual_pdf or not os.path.exists(actual_pdf):
                forms.alert("Failed to export PDF for preview.\n\nExport Status: {}\nOutput Path: {}\nSheet: {}".format(
                    export_ok, os.path.join(temp_dir, pdf_prefix + ".pdf"), getattr(sheet_element, 'SheetNumber', '-')))
                sr.set_status("Preview Error", is_error=True)
                return

            try:
                sz = os.path.getsize(actual_pdf)
                log_diag("Preview PDF exported successfully: {} ({} bytes)".format(actual_pdf, sz))
            except Exception:
                pass

            # 3. Convert page 0 of PDF to high-res PNG using native Windows WinRT
            ps1_path = os.path.join(os.path.dirname(__file__), "render_pdf.ps1")
            import subprocess
            import time
            cmd = ['powershell.exe', '-ExecutionPolicy', 'Bypass', '-WindowStyle', 'Hidden', '-File', ps1_path, '-PdfPath', actual_pdf, '-PngPath', png_out, '-Width', '1400']
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            proc = subprocess.Popen(cmd, startupinfo=startupinfo)
            start_t = time.time()
            while proc.poll() is None:
                System.Threading.Thread.Sleep(50)
                if time.time() - start_t > 10:
                    try: proc.kill()
                    except Exception: pass
                    break

            sr.set_status("")

            if os.path.exists(png_out) and os.path.getsize(png_out) > 0:
                self.preview_cache[cache_key] = png_out
                self.display_preview_image(png_out)
            else:
                # Direct fallback to system PDF viewer
                os.startfile(actual_pdf)
                sr.set_status("Opened in PDF Viewer")

        except Exception as ex:
            sr.set_status("Preview Error", is_error=True)
            forms.alert(str(ex))
        finally:
            if hasattr(self, 'BtnDoPreview'):
                self.BtnDoPreview.IsEnabled = True
            if hasattr(self, 'GridPreviewLoading'):
                self.GridPreviewLoading.Visibility = System.Windows.Visibility.Collapsed
            if cache_key in self.preview_cache and os.path.exists(self.preview_cache[cache_key]):
                if hasattr(self, 'GridPreviewPrompt'):
                    self.GridPreviewPrompt.Visibility = System.Windows.Visibility.Collapsed
                if hasattr(self, 'BtnDoPreview'):
                    self.BtnDoPreview.Visibility = System.Windows.Visibility.Collapsed
            else:
                if hasattr(self, 'GridPreviewPrompt'):
                    self.GridPreviewPrompt.Visibility = System.Windows.Visibility.Visible
                if hasattr(self, 'BtnDoPreview'):
                    self.BtnDoPreview.Visibility = System.Windows.Visibility.Visible

    def extract_mock_data(self, bg_doc, row):
        pi = getattr(bg_doc, "ProjectInformation", None)
        if pi:
            try:
                for p in pi.Parameters:
                    try:
                        p_name = p.Definition.Name if p.Definition else ""
                        if p_name:
                            val = _safe_get_param_val(p)
                            if val:
                                row.mock_doc.ProjectInformation.add_param(p_name, val)
                    except Exception:
                        pass
            except Exception:
                pass
                
        # 1. Add All Sheets
        all_sheets = DB.FilteredElementCollector(bg_doc).OfClass(DB.ViewSheet).ToElements()
        all_mock_list = []
        for v in all_sheets:
            try:
                if v.IsPlaceholder: continue
            except Exception:
                pass
            
            s_num = getattr(v, 'SheetNumber', '') or ''
            s_name = getattr(v, 'Name', '') or ''
            me = MockElement(s_name, s_num, v.UniqueId)
            
            # Explicitly guarantee Sheet Number & Sheet Name
            if s_num:
                me.add_param("Sheet Number", s_num)
            if s_name:
                me.add_param("Sheet Name", s_name)

            # Extract Sheet Collection (Revit 2025 native or Parameter)
            sheet_coll = ""
            try:
                if hasattr(v, "SheetCollectionId") and v.SheetCollectionId != DB.ElementId.InvalidElementId:
                    sc_elem = bg_doc.GetElement(v.SheetCollectionId)
                    if sc_elem and hasattr(sc_elem, "Name"):
                        sheet_coll = sc_elem.Name
            except Exception:
                pass
            if not sheet_coll:
                try:
                    p = v.LookupParameter("Sheet Collection")
                    if p and p.AsString():
                        sheet_coll = p.AsString().strip()
                except Exception:
                    pass
            me.sheet_collection = sheet_coll
            if sheet_coll:
                me.add_param("Sheet Collection", sheet_coll)

            # Extract revision
            try:
                rev_p = v.get_Parameter(DB.BuiltInParameter.SHEET_CURRENT_REVISION)
                if rev_p:
                    rev_val = _safe_get_param_val(rev_p)
                    if rev_val:
                        me.add_param("Current Revision", rev_val)
            except Exception:
                pass
                
            # Safely extract all sheet parameters
            try:
                for p in v.Parameters:
                    try:
                        p_name = p.Definition.Name if p.Definition else ""
                        if p_name:
                            val = _safe_get_param_val(p)
                            if val:
                                me.add_param(p_name, val)
                    except Exception:
                        pass
            except Exception:
                pass

            # Also extract Title Block parameters (drawing numbers, custom volume/code params)
            try:
                tbs = DB.FilteredElementCollector(bg_doc, v.Id).OfCategory(DB.BuiltInCategory.OST_TitleBlocks).ToElements()
                for tb in tbs:
                    for p in tb.Parameters:
                        try:
                            p_name = p.Definition.Name if p.Definition else ""
                            if p_name and not me.LookupParameter(p_name):
                                val = _safe_get_param_val(p)
                                if val:
                                    me.add_param(p_name, val)
                        except Exception:
                            pass
            except Exception:
                pass
                
            all_mock_list.append(me)
            
        all_mock_list = sorted(all_mock_list, key=lambda x: x.SheetNumber)
        row.sets_dict["<All Sheets>"] = all_mock_list
        
        # 2. Add Sheet Collections
        unique_collections = sorted(list(set(me.sheet_collection for me in all_mock_list if me.sheet_collection)))
        for c_name in unique_collections:
            coll_mock_list = [me for me in all_mock_list if me.sheet_collection == c_name]
            key_name = "[Collection] " + c_name
            row.sets_dict[key_name] = coll_mock_list
                
        # 3. Add Sheet Sets
        vss_collector = DB.FilteredElementCollector(bg_doc).OfClass(DB.ViewSheetSet).ToElements()
        for vss in vss_collector:
            mock_list = []
            for v in vss.Views:
                if v.ViewType == DB.ViewType.DrawingSheet:
                    s_num = getattr(v, 'SheetNumber', '') or ''
                    s_name = getattr(v, 'Name', '') or ''
                    me = MockElement(s_name, s_num, v.UniqueId)
                    if s_num:
                        me.add_param("Sheet Number", s_num)
                    if s_name:
                        me.add_param("Sheet Name", s_name)
                    
                    # Extract Sheet Collection
                    sheet_coll = ""
                    try:
                        if hasattr(v, "SheetCollectionId") and v.SheetCollectionId != DB.ElementId.InvalidElementId:
                            sc_elem = bg_doc.GetElement(v.SheetCollectionId)
                            if sc_elem and hasattr(sc_elem, "Name"):
                                sheet_coll = sc_elem.Name
                    except Exception:
                        pass
                    if not sheet_coll:
                        try:
                            p = v.LookupParameter("Sheet Collection")
                            if p and p.AsString():
                                sheet_coll = p.AsString().strip()
                        except Exception:
                            pass
                    me.sheet_collection = sheet_coll
                    if sheet_coll:
                        me.add_param("Sheet Collection", sheet_coll)

                    try:
                        rev_p = v.get_Parameter(DB.BuiltInParameter.SHEET_CURRENT_REVISION)
                        if rev_p:
                            rev_val = _safe_get_param_val(rev_p)
                            if rev_val:
                                me.add_param("Current Revision", rev_val)
                    except Exception:
                        pass
                    try:
                        for p in v.Parameters:
                            try:
                                p_name = p.Definition.Name if p.Definition else ""
                                if p_name:
                                    val = _safe_get_param_val(p)
                                    if val:
                                        me.add_param(p_name, val)
                            except Exception:
                                pass
                    except Exception:
                        pass
                    try:
                        tbs = DB.FilteredElementCollector(bg_doc, v.Id).OfCategory(DB.BuiltInCategory.OST_TitleBlocks).ToElements()
                        for tb in tbs:
                            for p in tb.Parameters:
                                try:
                                    p_name = p.Definition.Name if p.Definition else ""
                                    if p_name and not me.LookupParameter(p_name):
                                        val = _safe_get_param_val(p)
                                        if val:
                                            me.add_param(p_name, val)
                                except Exception:
                                    pass
                    except Exception:
                        pass
                    mock_list.append(me)
            mock_list = sorted(mock_list, key=lambda x: x.SheetNumber)
            key_name = "[Set] " + vss.Name
            row.sets_dict[key_name] = mock_list
            
        coll_keys = [k for k in sorted(row.sets_dict.keys()) if k.startswith("[Collection]")]
        set_keys = [k for k in sorted(row.sets_dict.keys()) if k.startswith("[Set]")]
        other_keys = [k for k in sorted(row.sets_dict.keys()) if k not in coll_keys and k not in set_keys and k != "<All Sheets>"]
        ordered_keys = ["<All Sheets>"] + coll_keys + set_keys + other_keys
        return ordered_keys

    def BtnAddFile_Click(self, sender, e):
        dlg = WinForms.OpenFileDialog()
        dlg.Filter = "Revit Files (*.rvt)|*.rvt"
        dlg.Multiselect = True
        if dlg.ShowDialog() == WinForms.DialogResult.OK:
            for f in dlg.FileNames:
                row = FileRow(f, self)
                self.rows.append(row)
                
                border = Border()
                border.BorderBrush = self.FindResource("BorderColor")
                border.BorderThickness = Thickness(0, 0, 0, 1)
                border.Padding = Thickness(0, 5, 0, 5)
                border.Child = row.main_container
                
                self.FileStack.Children.Add(border)
                self.do_events()
                
                row.set_status("Reading...", is_exporting=True)
                bg_doc = None
                should_close = False
                try:
                    bg_doc, should_close = get_or_open_document(row.file_path, close_worksets=False)
                    key = os.path.abspath(row.file_path).lower()
                    self.doc_cache[key] = (bg_doc, should_close)
                    
                    sets = self.extract_mock_data(bg_doc, row)
                    
                    row.cmb_set.ItemsSource = sets
                    if sets:
                        row.cmb_set.SelectedIndex = 0
                        
                    row.set_status("Ready")
                except Exception as ex:
                    row.set_status("Error loading sets: " + str(ex), is_error=True)
                    if should_close and bg_doc:
                        try: bg_doc.Close(False)
                        except: pass
                    forms.alert(str(ex) + '\n\n' + traceback.format_exc())

    def BtnClearAll_Click(self, sender, e):
        self.cleanup_cached_documents()
        self.FileStack.Children.Clear()
        self.rows = []
        self.selected_sheet = None
        self.preview_cache.clear()
        if hasattr(self, 'ImgPreview') and self.ImgPreview:
            self.ImgPreview.Source = None
            self.ImgPreview.Visibility = System.Windows.Visibility.Collapsed
        if hasattr(self, 'GridPreviewPrompt') and self.GridPreviewPrompt:
            self.GridPreviewPrompt.Visibility = System.Windows.Visibility.Visible
        if hasattr(self, 'TxtPreviewHint') and self.TxtPreviewHint:
            self.TxtPreviewHint.Text = "Click Preview to view"
        if hasattr(self, 'BtnDoPreview') and self.BtnDoPreview:
            self.BtnDoPreview.Visibility = System.Windows.Visibility.Visible
        for attr in ['TxtDetailNumber', 'TxtDetailName', 'TxtDetailCollection', 'TxtDetailExportName', 'TxtDetailModel']:
            if hasattr(self, attr):
                getattr(self, attr).Text = "-"

    def BtnExport_Click(self, sender, e):
        if not self.rows: return
        for row in self.rows:
            if not row.output_location or row.output_location == "Select Folder...":
                forms.alert("Please select output locations for all files.", title="Missing Location")
                return
        
        self.BtnExport.IsEnabled = False
        self._cancel_export = False
        is_check_print = self.RbCheckPrint.IsChecked
        
        archived_locations = set()
        first_folder = None
        total_exported_sheets = 0
        total_failed_sheets = 0
        total_skipped_sheets = 0

        for row in self.rows:
            if self._cancel_export: break
            
            row.main_container.BringIntoView()
            self.do_events()
            
            if not first_folder and row.output_location:
                first_folder = row.output_location

            # Archive previous exports in output_location if not already done in this session
            if row.output_location and row.output_location not in archived_locations:
                row.set_status("Archiving previous files...", is_exporting=True)
                try:
                    arch_sub = em_script.archive_previous_exports(row.output_location)
                    if arch_sub:
                        row.set_status("Archived to 00 PREVIOUS\\" + arch_sub)
                        self.do_events()
                except Exception:
                    pass
                archived_locations.add(row.output_location)

            row.set_status("Preparing file...", is_exporting=True)
            bg_doc = None
            should_close = False
            try:
                bg_doc, should_close = self.get_cached_document(row.file_path)
                
                em_script.doc = bg_doc
                
                pdf_items = []
                for s_row in row.sheet_rows:
                    if s_row.chk.IsChecked != True:
                        s_row.set_status("Skipped")
                        total_skipped_sheets += 1
                        continue
                        
                    sheet_element = bg_doc.GetElement(s_row.mock_sheet.UniqueId)
                    if sheet_element:
                        pdf_items.append({
                            "sheet": sheet_element,
                            "filename": s_row.generated_name,
                            "ui_row": s_row
                        })
                        s_row.set_status("Pending")
                
                if not pdf_items:
                    row.set_status("No sheets to export", is_error=True)
                    if should_close:
                        try: bg_doc.Close(False)
                        except: pass
                    continue
                
                row.set_status("Exporting Combined PDF...", is_exporting=True)
                comb_filename = "Combined_Set_{}.pdf".format(os.path.basename(row.file_path).replace('.rvt',''))
                
                # Wire ui_row so Revit ProgressChanged events directly update each sheet row
                mock_queue = [MockQueueItem(item["sheet"], item["filename"], ui_row=item["ui_row"]) for item in pdf_items]
                
                self.TxtPercent.Text = "Exporting Combined PDF..."
                self.ExportProgressBar.Value = 0
                self.do_events()
                
                em_script.export_combined_pdf_2022(row.output_location, mock_queue, comb_filename, get_zoom_fit_type(), 100, window_instance=self)
                
                for item in pdf_items:
                    item["ui_row"].set_status("Done" if is_check_print else "Combined PDF Done", is_done=True)
                
                # Generate Excel Transmittal / Drawing List
                try:
                    self.TxtPercent.Text = "Generating Excel Drawing List..."
                    self.do_events()
                    vms = [item.SheetVM for item in mock_queue]
                    em_script.generate_excel_transmittal(row.output_location, vms, bg_doc, comb_filename.replace('.pdf',''))
                except Exception as ex_tr:
                    log_diag("Excel transmittal note: " + str(ex_tr))
                
                # Export individual PDFs and DWGs if Full Set mode
                if not is_check_print:
                    row.set_status("Exporting CAD & Single PDFs...", is_exporting=True)
                    pdf_out_dir = os.path.join(row.output_location, "PDF")
                    dwg_out_dir = os.path.join(row.output_location, "DWG")
                    if not os.path.exists(pdf_out_dir):
                        try: os.makedirs(pdf_out_dir)
                        except Exception: pass
                    if not os.path.exists(dwg_out_dir):
                        try: os.makedirs(dwg_out_dir)
                        except Exception: pass

                    total_single = len(pdf_items)
                    for idx, item in enumerate(pdf_items):
                        if self._cancel_export: break
                        s_row = item["ui_row"]
                        sheet = item["sheet"]
                        fname = item["filename"]
                        
                        pct = int((float(idx) / total_single) * 100)
                        self.ExportProgressBar.Value = pct
                        self.TxtPercent.Text = "Exporting [{}/{}]: {} (PDF)".format(idx + 1, total_single, fname)
                        s_row.set_status("Exporting PDF...", is_exporting=True)
                        self.do_events()
                        
                        try:
                            em_script.export_pdf_2022(pdf_out_dir, sheet, fname, get_zoom_fit_type(), 100)
                        except Exception as ex_pdf:
                            log_diag("Single PDF error: " + str(ex_pdf))
                            
                        self.TxtPercent.Text = "Exporting [{}/{}]: {} (DWG)".format(idx + 1, total_single, fname)
                        s_row.set_status("Exporting CAD...", is_exporting=True)
                        self.do_events()
                        
                        try:
                            em_script.export_dwg(dwg_out_dir, sheet, fname, None)
                        except Exception as ex_dwg:
                            log_diag("DWG error: " + str(ex_dwg))
                            
                        s_row.set_status("Done", is_done=True)
                        total_exported_sheets += 1
                        self.do_events()
                else:
                    total_exported_sheets += len(pdf_items)
                
                if should_close:
                    try: bg_doc.Close(False)
                    except: pass
                row.set_status("Completed!", is_done=True)
                
            except Exception as ex:
                total_failed_sheets += len(row.sheet_rows)
                row.set_status("Error", is_error=True)
                if should_close and bg_doc:
                    try: bg_doc.Close(False)
                    except: pass
                log_diag("Export error: " + str(ex) + "\n" + traceback.format_exc())
                
        self.BtnExport.IsEnabled = True
        self.ExportProgressBar.Value = 100
        self.TxtPercent.Text = "Finished!"
        
        # Show Custom Export Completed Window if not cancelled
        if not self._cancel_export and first_folder:
            theme = "Dark"
            try:
                settings_path = os.path.join(export_mgr_dir, "naming_settings.json")
                if os.path.exists(settings_path):
                    with open(settings_path, 'r') as f:
                        settings = json.load(f)
                        theme = settings.get("theme", "Dark")
            except:
                pass
                
            if total_exported_sheets > 0 and total_failed_sheets == 0:
                msg = "Batch export completed successfully.\nTotal sheets exported: {}".format(total_exported_sheets)
            elif total_exported_sheets > 0:
                msg = "Batch export finished with warnings.\nSuccessfully exported: {}\nFailed: {}\nSkipped: {}".format(
                    total_exported_sheets, total_failed_sheets, total_skipped_sheets
                )
            elif total_failed_sheets > 0:
                msg = "Batch export failed.\nErrors encountered during export."
            else:
                msg = "No sheets were exported."
                
            try:
                cw = em_script.CustomExportCompletedWindow(first_folder, msg, theme)
                cw.ShowDialog()
            except Exception as ex_cw:
                log_diag("Completion window error: " + str(ex_cw))

def main():
    try:
        theme = "Dark"
        settings_path = os.path.join(export_mgr_dir, "naming_settings.json")
        if os.path.exists(settings_path):
            import json
            with open(settings_path, 'r') as f:
                try:
                    settings = json.load(f)
                    theme = settings.get("theme", "Dark")
                except:
                    pass
                    
        exp_name = 'UI_Light.xaml' if theme == 'Light' else 'UI.xaml'
        xaml_path = os.path.join(os.path.dirname(__file__), exp_name)
        
        form = BatchExportForm(xaml_path)
        form.ShowDialog()
    except Exception as ex:
        forms.alert('Failed to load UI:\n\n' + str(ex) + '\n\n' + traceback.format_exc(), title='UI Error')

main()