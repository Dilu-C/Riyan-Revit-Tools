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
from System.Windows import Thickness, GridLength, GridUnitType, HorizontalAlignment, VerticalAlignment, TextWrapping, Window, Application, CornerRadius
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

BG_DONE = SolidColorBrush(ColorConverter.ConvertFromString("#5CB85C"))
BG_EXPORTING = SolidColorBrush(ColorConverter.ConvertFromString("#FFB300"))
BG_ERROR = SolidColorBrush(ColorConverter.ConvertFromString("#E53935"))
TEXT_DARK = SolidColorBrush(ColorConverter.ConvertFromString("#111111"))
TEXT_WHITE = SolidColorBrush(System.Windows.Media.Colors.White)
BRUSH_DONE = BG_DONE
BRUSH_EXPORTING = BG_EXPORTING
BRUSH_ERROR = BG_ERROR

def get_zoom_fit_type():
    if hasattr(DB, "ZoomType") and hasattr(DB.ZoomType, "Zoom"):
        return DB.ZoomType.Zoom
    elif hasattr(DB, "PDFZoomType") and hasattr(DB.PDFZoomType, "Zoom"):
        return DB.PDFZoomType.Zoom
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

    # Avoid forced reloading of Revit links in background mode (saves memory and avoids network lag)
    log_diag("Document opened ready for export without forced link reloading.")

    return (bg_doc, True)

def pick_folder_dialog(title="Select Folder", initial_path=None):
    dlg = WinForms.FolderBrowserDialog()
    if hasattr(dlg, "UseDescriptionForTitle"):
        try:
            dlg.UseDescriptionForTitle = True
            if title:
                dlg.Description = title
        except Exception:
            pass
    if initial_path and os.path.exists(initial_path):
        dlg.SelectedPath = initial_path
    if dlg.ShowDialog() == WinForms.DialogResult.OK:
        return dlg.SelectedPath
    return None

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
        self.border.Background = SolidColorBrush(ColorConverter.ConvertFromString("#01000000"))
        self.border.Cursor = System.Windows.Input.Cursors.Hand
        
        self.grid = Grid()
        self.border.Child = self.grid
        
        from System.Windows.Data import Binding, BindingMode
        for i in range(7):
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
                    fixed_widths = {0: 380, 1: 180, 2: 200, 3: 160}
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
        
        self.border_status = Border()
        self.border_status.Padding = Thickness(6, 2, 6, 2)
        self.border_status.CornerRadius = CornerRadius(3)
        self.border_status.Background = SolidColorBrush(System.Windows.Media.Colors.Transparent)
        self.border_status.HorizontalAlignment = HorizontalAlignment.Center
        self.border_status.VerticalAlignment = VerticalAlignment.Center
        
        self.txt_status = TextBlock()
        self.txt_status.Text = "Pending"
        self.txt_status.FontWeight = System.Windows.FontWeights.SemiBold
        self.txt_status.VerticalAlignment = VerticalAlignment.Center
        self.txt_status.HorizontalAlignment = HorizontalAlignment.Center
        self.txt_status.TextAlignment = System.Windows.TextAlignment.Center
        self.txt_status.TextTrimming = System.Windows.TextTrimming.CharacterEllipsis
        if brush_dim: self.txt_status.Foreground = brush_dim
        
        self.border_status.Child = self.txt_status
        Grid.SetColumn(self.border_status, 6)
        self.grid.Children.Add(self.border_status)
        
        self.border.Focusable = True
        self.border.FocusVisualStyle = None
        
        # Context Menu matching Export Manager
        cm = System.Windows.Controls.ContextMenu()
        try:
            cm_style = self.form.FindResource("ThemeContextMenu")
            if cm_style: cm.Style = cm_style
        except:
            pass
        mi_style = None
        try:
            mi_style = self.form.FindResource("ThemeMenuItem")
        except:
            pass

        mi_preview = System.Windows.Controls.MenuItem()
        mi_preview.Header = u"👁  Preview Sheet (Double-Click)"
        if mi_style: mi_preview.Style = mi_style
        mi_preview.Click += lambda s, e: self.form.preview_sheet_row(self)
        cm.Items.Add(mi_preview)
        
        cm.Items.Add(System.Windows.Controls.Separator())
        
        mi_check = System.Windows.Controls.MenuItem()
        mi_check.Header = u"✓  Check Selected (Space)"
        if mi_style: mi_check.Style = mi_style
        mi_check.Click += lambda s, e: self.form.menu_check_selected(True)
        cm.Items.Add(mi_check)
        
        mi_uncheck = System.Windows.Controls.MenuItem()
        mi_uncheck.Header = u"☐  Uncheck Selected"
        if mi_style: mi_uncheck.Style = mi_style
        mi_uncheck.Click += lambda s, e: self.form.menu_check_selected(False)
        cm.Items.Add(mi_uncheck)
        
        mi_invert = System.Windows.Controls.MenuItem()
        mi_invert.Header = u"⇄  Invert Selected"
        if mi_style: mi_invert.Style = mi_style
        mi_invert.Click += lambda s, e: self.form.menu_invert_selected()
        cm.Items.Add(mi_invert)
        
        cm.Items.Add(System.Windows.Controls.Separator())
        
        mi_check_all = System.Windows.Controls.MenuItem()
        mi_check_all.Header = u"Select All Sheets"
        if mi_style: mi_check_all.Style = mi_style
        mi_check_all.Click += lambda s, e: self.form.menu_set_all_sheets(True)
        cm.Items.Add(mi_check_all)
        
        mi_uncheck_all = System.Windows.Controls.MenuItem()
        mi_uncheck_all.Header = u"Unselect All Sheets"
        if mi_style: mi_uncheck_all.Style = mi_style
        mi_uncheck_all.Click += lambda s, e: self.form.menu_set_all_sheets(False)
        cm.Items.Add(mi_uncheck_all)
        
        self.border.ContextMenu = cm
        self.border.PreviewMouseLeftButtonDown += self.on_mouse_down
        self.border.PreviewMouseRightButtonDown += self.on_mouse_right_down
        self.border.PreviewKeyDown += self.on_preview_key_down
        self.chk.PreviewKeyDown += self.on_preview_key_down

    def highlight(self, bg_brush, text_brush):
        self.border.Background = bg_brush
        self.txt_name.Foreground = text_brush
        if self.txt_status.Text in ["Pending", "Skipped", ""]:
            self.txt_status.Foreground = text_brush

    def unhighlight(self, brush_main, brush_dim):
        self.border.Background = SolidColorBrush(System.Windows.Media.Colors.Transparent)
        if brush_main:
            self.txt_name.Foreground = brush_main
        if brush_dim and self.txt_status.Text in ["Pending", "Skipped", ""]:
            self.txt_status.Foreground = brush_dim

    def on_chk_clicked(self, sender, e):
        is_checked = (self.chk.IsChecked == True)
        selected_sheets = getattr(self.form, 'selected_sheets', [])
        if self in selected_sheets and len(selected_sheets) > 1:
            for s in selected_sheets:
                s.chk.IsChecked = is_checked
                if s.parent_group:
                    s.parent_group.update_collection_checkbox()
                elif s.parent:
                    s.parent.update_master_checkbox()
        else:
            self.form.select_sheet_advanced(self, is_ctrl=False, is_shift=False)
            if self.parent_group:
                self.parent_group.update_collection_checkbox()
            elif self.parent:
                self.parent.update_master_checkbox()
        try:
            self.border.Focus()
        except:
            pass
        if hasattr(self.form, 'update_file_count'):
            self.form.update_file_count()

    def on_preview_key_down(self, sender, e):
        try:
            import System.Windows.Input as WinInput
            if e.Key == WinInput.Key.Space:
                self.form.toggle_selected_sheets_space()
                e.Handled = True
        except:
            pass

    def on_mouse_down(self, sender, e):
        if hasattr(e, "OriginalSource") and isinstance(e.OriginalSource, System.Windows.Controls.CheckBox):
            return
        try:
            import System.Windows.Input as WinInput
            WinInput.Keyboard.Focus(self.border)
        except:
            pass
        if hasattr(e, "ClickCount") and e.ClickCount == 2:
            self.form.preview_sheet_row(self)
            e.Handled = True
            return
        self.on_select(sender, e)

    def on_mouse_right_down(self, sender, e):
        if hasattr(e, "OriginalSource") and isinstance(e.OriginalSource, System.Windows.Controls.CheckBox):
            return
        try:
            import System.Windows.Input as WinInput
            WinInput.Keyboard.Focus(self.border)
        except:
            pass
        selected = getattr(self.form, 'selected_sheets', [])
        if self not in selected:
            self.form.select_sheet_advanced(self, is_ctrl=False, is_shift=False)

    def on_select(self, sender, e):
        if hasattr(e, "OriginalSource") and isinstance(e.OriginalSource, System.Windows.Controls.CheckBox):
            return
            
        import System.Windows.Input as WinInput
        modifiers = WinInput.Keyboard.Modifiers
        is_shift = (modifiers & WinInput.ModifierKeys.Shift) == WinInput.ModifierKeys.Shift
        is_ctrl = (modifiers & WinInput.ModifierKeys.Control) == WinInput.ModifierKeys.Control
        if not is_shift:
            is_shift = WinInput.Keyboard.IsKeyDown(WinInput.Key.LeftShift) or WinInput.Keyboard.IsKeyDown(WinInput.Key.RightShift)
        if not is_ctrl:
            is_ctrl = WinInput.Keyboard.IsKeyDown(WinInput.Key.LeftCtrl) or WinInput.Keyboard.IsKeyDown(WinInput.Key.RightCtrl)
                   
        self.form.select_sheet_advanced(self, is_ctrl=is_ctrl, is_shift=is_shift)
        
    def set_status(self, msg, is_done=False, is_exporting=False, is_error=False):
        clean_msg = msg or ""
        for tag in ["[Done] ", "[Exporting] ", "[Error] "]:
            if clean_msg.startswith(tag):
                clean_msg = clean_msg[len(tag):]
                
        brush_dim = self.form.FindResource("TextDim") or SolidColorBrush(ColorConverter.ConvertFromString("#888888"))

        if is_done or clean_msg == "Done":
            self.txt_status.Text = "Done"
            self.txt_status.Foreground = TEXT_DARK
            self.border_status.Background = BG_DONE
        elif clean_msg == "Exporting..." or (is_exporting and clean_msg in ["", "Exporting", "Exporting..."]):
            self.txt_status.Text = "Exporting..."
            self.txt_status.Foreground = TEXT_DARK
            self.border_status.Background = BG_EXPORTING
            try:
                self.border.BringIntoView()
            except:
                pass
        elif is_error or clean_msg == "Error":
            self.txt_status.Text = "Error"
            self.txt_status.Foreground = TEXT_WHITE
            self.border_status.Background = BG_ERROR
        elif clean_msg == "Skipped":
            self.txt_status.Text = "Skipped"
            self.txt_status.Foreground = brush_dim
            self.border_status.Background = SolidColorBrush(System.Windows.Media.Colors.Transparent)
        else:
            self.txt_status.Text = clean_msg if clean_msg else "Pending"
            self.txt_status.Foreground = brush_dim
            self.border_status.Background = SolidColorBrush(System.Windows.Media.Colors.Transparent)

        self.border_status.ToolTip = clean_msg
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
        for i in range(7):
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
                    fixed_widths = {0: 380, 1: 180, 2: 200, 3: 160}
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

class FolderGroupRow:
    def __init__(self, folder_name, form_instance):
        self.folder_name = folder_name
        self.form = form_instance
        self.file_rows = []
        self.is_expanded = True
        self._updating_checkbox = False

        is_dark = getattr(form_instance, 'is_dark', True)
        conv = ColorConverter.ConvertFromString
        brush = lambda c: SolidColorBrush(conv(c))

        self.container = StackPanel()
        self.container.Orientation = Orientation.Vertical
        self.container.Margin = Thickness(0, 4, 0, 4)

        # Folder Header Bar
        self.header_border = Border()
        if is_dark:
            self.header_border.Background = brush("#252A36")
            self.header_border.BorderBrush = brush("#3B4354")
            fg_title = brush("#FFFFFF")
            fg_btn = brush("#FFFFFF")
            badge_bg = brush("#1E293B")
            badge_fg = brush("#38BDF8")
        else:
            self.header_border.Background = brush("#EAEFF6")
            self.header_border.BorderBrush = brush("#CBD5E1")
            fg_title = brush("#0F172A")
            fg_btn = brush("#0F172A")
            badge_bg = brush("#DBEAFE")
            badge_fg = brush("#1E40AF")

        self.header_border.BorderThickness = Thickness(1)
        self.header_border.CornerRadius = CornerRadius(6)
        self.header_border.Padding = Thickness(8, 5, 8, 5)
        self.header_border.Cursor = System.Windows.Input.Cursors.Hand
        self.header_border.MouseLeftButtonDown += self.on_header_click

        grid = Grid()
        cd0 = System.Windows.Controls.ColumnDefinition()
        cd0.Width = GridLength(1, GridUnitType.Star)
        cd1 = System.Windows.Controls.ColumnDefinition()
        cd1.Width = GridLength.Auto
        grid.ColumnDefinitions.Add(cd0)
        grid.ColumnDefinitions.Add(cd1)

        sp_left = StackPanel()
        sp_left.Orientation = Orientation.Horizontal
        sp_left.VerticalAlignment = VerticalAlignment.Center

        self.chk = System.Windows.Controls.CheckBox()
        self.chk.IsChecked = True
        self.chk.IsThreeState = True
        self.chk.VerticalAlignment = VerticalAlignment.Center
        self.chk.Margin = Thickness(0, 0, 8, 0)
        self.chk.Click += self.on_chk_clicked
        sp_left.Children.Add(self.chk)

        self.btn_expand = Button()
        self.btn_expand.Content = "-"
        self.btn_expand.Width = 22
        self.btn_expand.Height = 22
        self.btn_expand.Background = SolidColorBrush(System.Windows.Media.Colors.Transparent)
        self.btn_expand.BorderThickness = Thickness(0)
        self.btn_expand.FontWeight = System.Windows.FontWeights.Bold
        self.btn_expand.FontSize = 13
        self.btn_expand.Foreground = fg_btn
        self.btn_expand.Cursor = System.Windows.Input.Cursors.Hand
        self.btn_expand.Click += self.on_expand
        sp_left.Children.Add(self.btn_expand)

        self.txt_title = TextBlock()
        self.txt_title.Text = "📁  " + self.folder_name
        self.txt_title.FontWeight = System.Windows.FontWeights.Bold
        self.txt_title.FontSize = 12
        self.txt_title.VerticalAlignment = VerticalAlignment.Center
        self.txt_title.Margin = Thickness(6, 0, 10, 0)
        self.txt_title.Foreground = fg_title
        sp_left.Children.Add(self.txt_title)

        bd_badge = Border()
        bd_badge.Background = badge_bg
        bd_badge.CornerRadius = CornerRadius(4)
        bd_badge.Padding = Thickness(7, 1, 7, 2)
        bd_badge.VerticalAlignment = VerticalAlignment.Center

        self.txt_count = TextBlock()
        self.txt_count.Text = "0 Files"
        self.txt_count.FontSize = 10
        self.txt_count.FontWeight = System.Windows.FontWeights.Bold
        self.txt_count.Foreground = badge_fg
        bd_badge.Child = self.txt_count
        sp_left.Children.Add(bd_badge)

        Grid.SetColumn(sp_left, 0)
        grid.Children.Add(sp_left)

        self.header_border.Child = grid
        self.container.Children.Add(self.header_border)

        # Children stack for FileRow borders
        self.child_stack = StackPanel()
        self.child_stack.Orientation = Orientation.Vertical
        self.child_stack.Margin = Thickness(0, 2, 0, 2)
        self.container.Children.Add(self.child_stack)

    def on_header_click(self, sender, e):
        if hasattr(e, "OriginalSource") and (e.OriginalSource == self.chk or e.OriginalSource == self.btn_expand):
            return
        self.on_expand(sender, e)

    def on_expand(self, sender, e):
        self.is_expanded = not self.is_expanded
        self.btn_expand.Content = "-" if self.is_expanded else "+"
        self.child_stack.Visibility = System.Windows.Visibility.Visible if self.is_expanded else System.Windows.Visibility.Collapsed
        try:
            self.form.Activate()
        except Exception:
            pass

    def expand(self):
        if not self.is_expanded:
            self.on_expand(None, None)

    def collapse(self):
        if self.is_expanded:
            self.on_expand(None, None)

    def on_chk_clicked(self, sender, e):
        if self._updating_checkbox:
            return
        val = (self.chk.IsChecked == True)
        self.chk.IsChecked = val
        for r in self.file_rows:
            if getattr(r, 'chk_all', None):
                r.chk_all.IsChecked = val
                r.on_chk_all_clicked(sender, e)
        self.form.update_file_count()

    def update_folder_checkbox(self):
        if self._updating_checkbox:
            return
        self._updating_checkbox = True
        try:
            total = len(self.file_rows)
            if total == 0:
                self.chk.IsChecked = False
                return
            checked = sum(1 for r in self.file_rows if getattr(r, 'chk_all', None) and r.chk_all.IsChecked == True)
            unchecked = sum(1 for r in self.file_rows if getattr(r, 'chk_all', None) and r.chk_all.IsChecked == False)
            if checked == total:
                self.chk.IsChecked = True
            elif unchecked == total:
                self.chk.IsChecked = False
            else:
                self.chk.IsChecked = None
        finally:
            self._updating_checkbox = False

    def add_file_row(self, file_row):
        file_row.folder_group = self
        self.file_rows.append(file_row)

        border = Border()
        border.BorderBrush = self.form.FindResource("BorderColor")
        border.BorderThickness = Thickness(0, 0, 0, 1)
        border.Padding = Thickness(0, 4, 0, 4)
        border.Child = file_row.main_container

        self.child_stack.Children.Add(border)
        count = len(self.file_rows)
        self.txt_count.Text = "{} File{}".format(count, "s" if count != 1 else "")
        self.update_folder_checkbox()

class FileRow:
    def __init__(self, file_path, form_instance):
        self.file_path = file_path
        self.form = form_instance
        self.profiles = form_instance.profiles
        self.output_location = os.path.dirname(os.path.abspath(self.file_path))
        self.mock_doc = MockDoc()
        self.sets_dict = {}
        self.sheet_rows = []
        self.collection_groups = []
        self.is_expanded = False
        self._updating_master = False
        self.sheets_loaded = False
        self._sheet_set_name = "PRINT"
        
        brush_main = form_instance.FindResource("TextMain")
        brush_dim = form_instance.FindResource("TextDim")
        btn_style = form_instance.FindResource("SecondaryBtn")
        
        self.main_container = StackPanel()
        
        self.row_border = Border()
        self.row_border.BorderThickness = Thickness(0, 0, 0, 1)
        self.row_border.BorderBrush = form_instance.FindResource("BorderColor")
        self.row_border.Padding = Thickness(4, 3, 4, 3)
        self.row_border.Background = SolidColorBrush(ColorConverter.ConvertFromString("#01000000"))
        self.row_border.Cursor = System.Windows.Input.Cursors.Hand
        self.row_border.Focusable = True
        self.row_border.FocusVisualStyle = None

        self.grid = Grid()
        self.grid.Margin = Thickness(0, 0, 0, 0)
        self.row_border.Child = self.grid
        self.main_container.Children.Add(self.row_border)
        
        from System.Windows.Data import Binding, BindingMode
        for i in range(7):
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
                    fixed_widths = {0: 380, 1: 180, 2: 200, 3: 160}
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
        self.chk_all.IsChecked = True
        self.chk_all.IsThreeState = True
        self.chk_all.VerticalAlignment = VerticalAlignment.Center
        self.chk_all.Margin = Thickness(5, 0, 5, 0)
        self.chk_all.Click += self.on_chk_all_clicked
        sp_file.Children.Add(self.chk_all)
        
        self.btn_expand = Button()
        self.btn_expand.Content = "+"
        self.btn_expand.Width = 20
        self.btn_expand.Height = 20
        self.btn_expand.Background = SolidColorBrush(System.Windows.Media.Colors.Transparent)
        self.btn_expand.BorderThickness = Thickness(0)
        self.btn_expand.Foreground = brush_main if brush_main else SolidColorBrush(System.Windows.Media.Colors.White)
        self.btn_expand.Click += self.on_expand
        self.btn_expand.Visibility = System.Windows.Visibility.Visible
        self.btn_expand.Cursor = System.Windows.Input.Cursors.Hand
        sp_file.Children.Add(self.btn_expand)
        
        self.txt_file = TextBlock()
        self.txt_file.Text = os.path.basename(self.file_path)
        self.txt_file.ToolTip = self.file_path
        self.txt_file.FontWeight = System.Windows.FontWeights.SemiBold
        self.txt_file.TextTrimming = System.Windows.TextTrimming.CharacterEllipsis
        sp_file.ClipToBounds = True
        self.txt_file.VerticalAlignment = VerticalAlignment.Center
        if brush_main: self.txt_file.Foreground = brush_main
        self.txt_file.Cursor = System.Windows.Input.Cursors.Arrow
        sp_file.Children.Add(self.txt_file)
        
        Grid.SetColumn(sp_file, 0)
        self.grid.Children.Add(sp_file)
        
        self.cmb_set = ComboBox()
        self.cmb_set.IsEditable = True
        self.cmb_set.Text = "PRINT"
        self.cmb_set.VerticalAlignment = VerticalAlignment.Center
        self.cmb_set.Margin = Thickness(5,0,5,0)
        self.cmb_set.SelectionChanged += self.on_options_changed
        Grid.SetColumn(self.cmb_set, 2)
        self.grid.Children.Add(self.cmb_set)
        
        loc_grid = Grid()
        loc_grid.ColumnDefinitions.Add(System.Windows.Controls.ColumnDefinition())
        cd_btn = System.Windows.Controls.ColumnDefinition()
        cd_btn.Width = GridLength(35, GridUnitType.Pixel)
        loc_grid.ColumnDefinitions.Add(cd_btn)
        
        self.txt_loc = TextBlock()
        self.txt_loc.Text = os.path.basename(self.output_location) or self.output_location
        self.txt_loc.ToolTip = self.output_location
        self.txt_loc.VerticalAlignment = VerticalAlignment.Center
        if brush_main: self.txt_loc.Foreground = brush_main
        Grid.SetColumn(self.txt_loc, 0)
        loc_grid.Children.Add(self.txt_loc)
        
        self.btn_browse = Button()
        self.btn_browse.Content = "..."
        if btn_style: self.btn_browse.Style = btn_style
        self.btn_browse.Height = 24
        self.btn_browse.Click += self.on_browse
        Grid.SetColumn(self.btn_browse, 1)
        loc_grid.Children.Add(self.btn_browse)
        
        Grid.SetColumn(loc_grid, 4)
        loc_grid.Margin = Thickness(5,0,5,0)
        self.grid.Children.Add(loc_grid)
        
        self.border_status = Border()
        self.border_status.Padding = Thickness(6, 2, 6, 2)
        self.border_status.CornerRadius = CornerRadius(3)
        self.border_status.Background = SolidColorBrush(System.Windows.Media.Colors.Transparent)
        self.border_status.HorizontalAlignment = HorizontalAlignment.Center
        self.border_status.VerticalAlignment = VerticalAlignment.Center
        
        self.txt_status = TextBlock()
        self.txt_status.Text = "Ready"
        self.txt_status.FontWeight = System.Windows.FontWeights.SemiBold
        self.txt_status.VerticalAlignment = VerticalAlignment.Center
        self.txt_status.HorizontalAlignment = HorizontalAlignment.Center
        self.txt_status.TextAlignment = System.Windows.TextAlignment.Center
        self.txt_status.TextTrimming = System.Windows.TextTrimming.CharacterEllipsis
        if brush_dim: self.txt_status.Foreground = brush_dim
        
        self.border_status.Child = self.txt_status
        Grid.SetColumn(self.border_status, 6)
        self.grid.Children.Add(self.border_status)
        
        self.sheet_stack = StackPanel()
        self.sheet_stack.Visibility = System.Windows.Visibility.Collapsed
        self.main_container.Children.Add(self.sheet_stack)

        # Wire mouse & key events on row_border
        self.row_border.MouseLeftButtonDown += self.on_mouse_down
        self.row_border.MouseRightButtonDown += self.on_mouse_right_down
        self.row_border.MouseEnter += self.on_mouse_enter
        self.row_border.MouseLeave += self.on_mouse_leave
        self.row_border.PreviewKeyDown += self.on_preview_key_down

        # Context menu for model row
        cm = System.Windows.Controls.ContextMenu()
        try:
            cm_style = self.form.FindResource("ThemeContextMenu")
            if cm_style: cm.Style = cm_style
        except: pass
        mi_style = None
        try:
            mi_style = self.form.FindResource("ThemeMenuItem")
        except: pass

        mi_check = System.Windows.Controls.MenuItem()
        mi_check.Header = u"✓  Check Selected (Space)"
        if mi_style: mi_check.Style = mi_style
        mi_check.Click += lambda s, e: self.form.menu_check_selected(True)
        cm.Items.Add(mi_check)
        
        mi_uncheck = System.Windows.Controls.MenuItem()
        mi_uncheck.Header = u"☐  Uncheck Selected"
        if mi_style: mi_uncheck.Style = mi_style
        mi_uncheck.Click += lambda s, e: self.form.menu_check_selected(False)
        cm.Items.Add(mi_uncheck)
        
        mi_invert = System.Windows.Controls.MenuItem()
        mi_invert.Header = u"⇄  Invert Selected"
        if mi_style: mi_invert.Style = mi_style
        mi_invert.Click += lambda s, e: self.form.menu_invert_selected()
        cm.Items.Add(mi_invert)
        
        cm.Items.Add(System.Windows.Controls.Separator())
        
        mi_check_all = System.Windows.Controls.MenuItem()
        mi_check_all.Header = u"Select All Models"
        if mi_style: mi_check_all.Style = mi_style
        mi_check_all.Click += lambda s, e: self.form.menu_set_all_sheets(True)
        cm.Items.Add(mi_check_all)

        mi_uncheck_all = System.Windows.Controls.MenuItem()
        mi_uncheck_all.Header = u"Deselect All Models"
        if mi_style: mi_uncheck_all.Style = mi_style
        mi_uncheck_all.Click += lambda s, e: self.form.menu_set_all_sheets(False)
        cm.Items.Add(mi_uncheck_all)

        self.row_border.ContextMenu = cm

    def on_mouse_enter(self, sender, e):
        if not getattr(self, 'is_selected', False):
            is_dark = getattr(self.form, 'is_dark', True)
            hover_color = "#1E2533" if is_dark else "#E2E8F0"
            self.row_border.Background = SolidColorBrush(ColorConverter.ConvertFromString(hover_color))

    def on_mouse_leave(self, sender, e):
        if not getattr(self, 'is_selected', False):
            self.row_border.Background = SolidColorBrush(ColorConverter.ConvertFromString("#01000000"))

    def on_mouse_down(self, sender, e):
        src = getattr(e, "OriginalSource", None)
        if src:
            parent = src
            while parent and parent != self.row_border:
                if isinstance(parent, (System.Windows.Controls.CheckBox, System.Windows.Controls.ComboBox, System.Windows.Controls.Button, System.Windows.Controls.TextBox)):
                    return
                parent = getattr(parent, "Parent", None)

        try:
            import System.Windows.Input as WinInput
            WinInput.Keyboard.Focus(self.row_border)
        except:
            pass

        if hasattr(e, "ClickCount") and e.ClickCount == 2:
            self.toggle_check()
            return

        import System.Windows.Input as WinInput
        modifiers = WinInput.Keyboard.Modifiers
        is_shift = (modifiers & WinInput.ModifierKeys.Shift) == WinInput.ModifierKeys.Shift
        is_ctrl = (modifiers & WinInput.ModifierKeys.Control) == WinInput.ModifierKeys.Control
        if not is_shift:
            is_shift = WinInput.Keyboard.IsKeyDown(WinInput.Key.LeftShift) or WinInput.Keyboard.IsKeyDown(WinInput.Key.RightShift)
        if not is_ctrl:
            is_ctrl = WinInput.Keyboard.IsKeyDown(WinInput.Key.LeftCtrl) or WinInput.Keyboard.IsKeyDown(WinInput.Key.RightCtrl)

        self.form.select_model_row_advanced(self, is_ctrl=is_ctrl, is_shift=is_shift)

    def on_mouse_right_down(self, sender, e):
        src = getattr(e, "OriginalSource", None)
        if src:
            parent = src
            while parent and parent != self.row_border:
                if isinstance(parent, (System.Windows.Controls.CheckBox, System.Windows.Controls.ComboBox, System.Windows.Controls.Button, System.Windows.Controls.TextBox)):
                    return
                parent = getattr(parent, "Parent", None)
        try:
            import System.Windows.Input as WinInput
            WinInput.Keyboard.Focus(self.row_border)
        except:
            pass
        selected = getattr(self.form, 'selected_model_rows', [])
        if self not in selected:
            self.form.select_model_row_advanced(self, is_ctrl=False, is_shift=False)

    def on_preview_key_down(self, sender, e):
        try:
            import System.Windows.Input as WinInput
            if e.Key == WinInput.Key.Space:
                self.form.toggle_selected_sheets_space()
                e.Handled = True
        except:
            pass

    def toggle_check(self):
        new_val = not (self.chk_all.IsChecked == True)
        self.chk_all.IsChecked = new_val
        self.on_chk_all_clicked(None, None)

    def highlight(self, select_brush, text_brush):
        self.is_selected = True
        self.row_border.Background = select_brush
        if text_brush:
            self.txt_file.Foreground = text_brush

    def unhighlight(self, brush_main, brush_dim):
        self.is_selected = False
        self.row_border.Background = SolidColorBrush(ColorConverter.ConvertFromString("#01000000"))
        if brush_main:
            self.txt_file.Foreground = brush_main

    def on_chk_all_clicked(self, sender, e):
        val = (self.chk_all.IsChecked == True)
        self.chk_all.IsChecked = val
        for cg in getattr(self, 'collection_groups', []):
            cg.set_checked_state(val)
        for sr in self.sheet_rows:
            sr.chk.IsChecked = val
        if hasattr(self.form, 'update_file_count'):
            self.form.update_file_count()
        if getattr(self, 'folder_group', None):
            self.folder_group.update_folder_checkbox()

    def update_master_checkbox(self):
        checked = sum(1 for sr in self.sheet_rows if sr.chk.IsChecked == True)
        total = len(self.sheet_rows)
        if total > 0 and checked == total:
            self.chk_all.IsChecked = True
        elif checked == 0:
            self.chk_all.IsChecked = False
        else:
            self.chk_all.IsChecked = None
        if hasattr(self.form, 'update_file_count'):
            self.form.update_file_count()
        if getattr(self, 'folder_group', None):
            self.folder_group.update_folder_checkbox()

    def get_sheet_set_name(self):
        if hasattr(self, 'cmb_set') and self.cmb_set:
            if self.cmb_set.SelectedItem:
                return str(self.cmb_set.SelectedItem).strip()
            if self.cmb_set.Text:
                return str(self.cmb_set.Text).strip()
        return getattr(self, '_sheet_set_name', "PRINT")

    def set_sheet_set_name(self, name):
        self._sheet_set_name = name
        if hasattr(self, 'cmb_set') and self.cmb_set:
            clean_target = str(name).replace("[Set] ", "").strip().lower()
            matched_idx = -1
            if self.cmb_set.ItemsSource:
                for idx, s in enumerate(self.cmb_set.ItemsSource):
                    clean_s = str(s).replace("[Set] ", "").strip().lower()
                    if clean_target == clean_s:
                        matched_idx = idx
                        break
                if matched_idx == -1:
                    for idx, s in enumerate(self.cmb_set.ItemsSource):
                        clean_s = str(s).replace("[Set] ", "").strip().lower()
                        if clean_target in clean_s or clean_s in clean_target:
                            matched_idx = idx
                            break
            if matched_idx >= 0:
                self.cmb_set.SelectedIndex = matched_idx
                if getattr(self, 'sheets_loaded', False):
                    self.on_options_changed(None, None)
            else:
                self.cmb_set.Text = name

    def expand(self):
        if not getattr(self, 'is_expanded', False):
            self.on_expand(None, None)

    def collapse(self):
        if getattr(self, 'is_expanded', False):
            self.on_expand(None, None)

    def load_sheets_on_demand(self):
        self.set_status("Loading...")
        self.form.do_events()
        bg_doc = None
        should_close = False
        try:
            bg_doc, should_close = self.form.get_cached_document(self.file_path)
            sets, default_idx = self.form.extract_mock_data(bg_doc, self)
            self.cmb_set.ItemsSource = sets
            
            cur_target = self.get_sheet_set_name()
            matched_idx = -1
            clean_cur = cur_target.replace("[Set] ", "").strip().lower()
            for idx, s in enumerate(sets):
                clean_s = str(s).replace("[Set] ", "").strip().lower()
                if clean_cur == clean_s or clean_cur in clean_s:
                    matched_idx = idx
                    break
                    
            if matched_idx >= 0:
                self.cmb_set.SelectedIndex = matched_idx
            else:
                self.cmb_set.Text = cur_target
                if sets and 0 <= default_idx < len(sets):
                    self.cmb_set.SelectedIndex = default_idx
                    
            self.sheets_loaded = True
            self.set_status("Ready")
            try:
                self.form.Activate()
            except:
                pass
        except Exception as ex:
            self.set_status("Ready")
        finally:
            if should_close and bg_doc:
                try:
                    if getattr(bg_doc, 'IsValidObject', True):
                        bg_doc.Close(False)
                except Exception:
                    pass
            try:
                self.form.Activate()
            except:
                pass

    def on_expand(self, sender, e):
        self.is_expanded = not self.is_expanded
        self.btn_expand.Content = "-" if self.is_expanded else "+"
        if self.is_expanded and not getattr(self, 'sheets_loaded', False):
            self.load_sheets_on_demand()
        try:
            self.form.Activate()
        except:
            pass
        self.sheet_stack.Visibility = System.Windows.Visibility.Visible if self.is_expanded else System.Windows.Visibility.Collapsed

    def set_output_location(self, new_dir):
        if not new_dir:
            return
        self.output_location = os.path.normpath(new_dir)
        self.txt_loc.Text = os.path.basename(self.output_location) or self.output_location
        self.txt_loc.ToolTip = self.output_location

    def on_browse(self, sender, e):
        sel = pick_folder_dialog("Select Output Location", self.output_location)
        if sel:
            self.set_output_location(sel)
            
    def set_status(self, msg, is_done=False, is_exporting=False, is_error=False):
        clean_msg = msg or ""
        for tag in ["[Done] ", "[Exporting] ", "[Error] "]:
            if clean_msg.startswith(tag):
                clean_msg = clean_msg[len(tag):]
                
        brush_dim = self.form.FindResource("TextDim") or SolidColorBrush(ColorConverter.ConvertFromString("#888888"))

        if is_done or clean_msg == "Done":
            self.txt_status.Text = "Done"
            self.txt_status.Foreground = TEXT_DARK
            self.border_status.Background = BG_DONE
        elif clean_msg == "Exporting..." or (is_exporting and clean_msg in ["", "Exporting", "Exporting..."]):
            self.txt_status.Text = "Exporting..."
            self.txt_status.Foreground = TEXT_DARK
            self.border_status.Background = BG_EXPORTING
        elif is_error or clean_msg == "Error":
            self.txt_status.Text = "Error"
            self.txt_status.Foreground = TEXT_WHITE
            self.border_status.Background = BG_ERROR
        elif clean_msg.startswith("Skipped"):
            self.txt_status.Text = "Skipped"
            self.txt_status.Foreground = brush_dim
            self.border_status.Background = SolidColorBrush(System.Windows.Media.Colors.Transparent)
        elif clean_msg in ["Ready", "Pending", "Loading...", "Reading..."]:
            self.txt_status.Text = clean_msg
            self.txt_status.Foreground = brush_dim
            self.border_status.Background = SolidColorBrush(System.Windows.Media.Colors.Transparent)
        else:
            self.txt_status.Text = clean_msg
            self.txt_status.Foreground = brush_dim
            self.border_status.Background = SolidColorBrush(System.Windows.Media.Colors.Transparent)

        self.border_status.ToolTip = clean_msg
        self.form.do_events()
        
    def on_options_changed(self, sender, e):
        try:
            if not self.cmb_set.SelectedItem:
                return
                
            set_name = self.cmb_set.SelectedItem
            profile_name = None
            if hasattr(self.form, 'CmbGlobalProfile') and self.form.CmbGlobalProfile and self.form.CmbGlobalProfile.SelectedItem:
                profile_name = str(self.form.CmbGlobalProfile.SelectedItem)
            elif hasattr(self, 'cmb_profile') and self.cmb_profile and self.cmb_profile.SelectedItem:
                profile_name = str(self.cmb_profile.SelectedItem)
            if not profile_name and self.form.profiles:
                profile_name = self.form.profiles[0]
                
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
                    s_row.chk.IsChecked = True
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
                        s_row.chk.IsChecked = True
                        self.sheet_rows.append(s_row)
                        c_group.add_sheet_row(s_row)
                    c_group.update_collection_checkbox()
                        
            self.update_master_checkbox()
        except Exception as ex:
            import traceback
            forms.alert(str(ex) + '\n\n' + traceback.format_exc(), title='Options Error')

class BatchExportForm(forms.WPFWindow):
    def __init__(self, xaml_file_name):
        forms.WPFWindow.__init__(self, xaml_file_name)
        
        # Pin window as child/owned by Revit so it NEVER falls behind Revit window during background document loading
        try:
            self.SourceInitialized += self.on_source_initialized
            import System.Windows.Interop as Interop
            revit_handle = getattr(__revit__, "MainWindowHandle", None)
            if not revit_handle:
                import System.Diagnostics
                revit_handle = System.Diagnostics.Process.GetCurrentProcess().MainWindowHandle
            if revit_handle:
                Interop.WindowInteropHelper(self).Owner = revit_handle
        except Exception as ex:
            log_diag("WindowInteropHelper Owner error: " + str(ex))

        self.is_dark = not ("UI_Light" in str(xaml_file_name))
        self.current_theme = "Dark" if self.is_dark else "Light"

        try:
            import System
            from System.Windows.Media.Imaging import BitmapImage
            from System import Uri
            tab_dir = os.path.dirname(os.path.dirname(__commandpath__))
            logo_path = os.path.join(tab_dir, "System.panel", "About.pushbutton", "logo.png")
            if not os.path.exists(logo_path):
                logo_path = os.path.join(os.path.dirname(__commandpath__), "logo.png")
            if not os.path.exists(logo_path):
                logo_path = os.path.join(tab_dir, "Coordination.panel", "ChangeHostLevel.pushbutton", "logo.png")
            if os.path.exists(logo_path) and hasattr(self, 'TitleLogo') and self.TitleLogo:
                self.TitleLogo.Source = BitmapImage(Uri(logo_path))
        except Exception as e:
            log_diag("Logo load error: " + str(e))

        self.rows = []
        self.folder_groups = []
        self.base_scan_dir = None
        self.outgoing_root_dir = None
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

        # Wire Global Naming Profile
        if hasattr(self, 'CmbGlobalProfile') and self.CmbGlobalProfile:
            self.CmbGlobalProfile.ItemsSource = self.profiles
            if self.profiles:
                self.CmbGlobalProfile.SelectedIndex = 0
            self.CmbGlobalProfile.SelectionChanged += self.on_global_profile_changed

        # Wire Master Sheet Set from Active Revit Document (Instant, 0.001s, no background open)
        active_sets = ["<All Sheets>", "PRINT"]
        try:
            active_doc = getattr(revit, "doc", None)
            if active_doc:
                col = DB.FilteredElementCollector(active_doc).OfClass(DB.ViewSheetSet)
                for s in col:
                    name = getattr(s, "Name", None)
                    if name and name not in active_sets:
                        active_sets.append(name)
        except Exception as ex:
            log_diag("Error querying active doc sheet sets: " + str(ex))

        if hasattr(self, 'CmbMasterSet') and self.CmbMasterSet:
            self.CmbMasterSet.ItemsSource = active_sets
            self.CmbMasterSet.Text = "PRINT"

        if hasattr(self, 'TxtFileCount') and self.TxtFileCount:
            self.TxtFileCount.Text = "0 Files Loaded"

        if hasattr(self, 'ImgPreview') and self.ImgPreview:
            self.ImgPreview.MouseLeftButtonDown += self.on_preview_image_click

        self.doc_cache = {}
        self.selected_sheets = []
        self.selection_anchor = None
        self.selected_model_rows = []
        self.model_selection_anchor = None
        self.selected_model_row = None
        class DummyQueue:
            class DummyItems:
                def Refresh(self): pass
            Items = DummyItems()
        self.GridQueue = DummyQueue()
        try:
            self.Closing += self.on_window_closing
            self.Closed += self.on_window_closed
            self.PreviewKeyDown += self.Window_PreviewKeyDown
            self.KeyDown += self.Window_PreviewKeyDown
            if hasattr(self, 'FileStack') and self.FileStack:
                self.FileStack.PreviewKeyDown += self.Window_PreviewKeyDown
        except Exception as ex:
            log_diag("Error wiring window events: " + str(ex))

        # Wire log resizer splitter
        self.is_resizing_log = False
        self.log_start_y = 0
        self.log_start_h = 85
        if hasattr(self, 'SplitLogs') and self.SplitLogs:
            self.SplitLogs.MouseLeftButtonDown += self.on_split_log_down
            self.SplitLogs.MouseMove += self.on_split_log_move
            self.SplitLogs.MouseLeftButtonUp += self.on_split_log_up
            self.SplitLogs.MouseEnter += self.on_split_log_enter
            self.SplitLogs.MouseLeave += self.on_split_log_leave

        self.log("Dilu BIM Automation initialized.")
        self.log("Zero Data Loss Architecture active: Double-verification backup enabled.")

    def on_source_initialized(self, sender, e):
        try:
            import System.Windows.Interop as Interop
            revit_handle = getattr(__revit__, "MainWindowHandle", None)
            if not revit_handle:
                import System.Diagnostics
                revit_handle = System.Diagnostics.Process.GetCurrentProcess().MainWindowHandle
            if revit_handle:
                Interop.WindowInteropHelper(self).Owner = revit_handle
        except Exception:
            pass

    def on_split_log_enter(self, sender, e):
        if hasattr(self, 'HandleLogs') and self.HandleLogs:
            is_dark = getattr(self, 'is_dark', True)
            self.HandleLogs.Background = SolidColorBrush(ColorConverter.ConvertFromString("#38BDF8" if is_dark else "#2563EB"))

    def on_split_log_leave(self, sender, e):
        if not getattr(self, 'is_resizing_log', False) and hasattr(self, 'HandleLogs') and self.HandleLogs:
            border_brush = self.FindResource("BorderColor")
            if border_brush:
                self.HandleLogs.Background = border_brush

    def on_split_log_down(self, sender, e):
        if hasattr(e, "ClickCount") and e.ClickCount == 2:
            if hasattr(self, 'CardLogs') and self.CardLogs:
                if self.CardLogs.ActualHeight > 130:
                    self.CardLogs.Height = 85
                else:
                    self.CardLogs.Height = 220
            return
        self.is_resizing_log = True
        self.log_start_y = e.GetPosition(self).Y
        if hasattr(self, 'CardLogs') and self.CardLogs:
            self.log_start_h = self.CardLogs.ActualHeight
        self.SplitLogs.CaptureMouse()

    def on_split_log_move(self, sender, e):
        if getattr(self, 'is_resizing_log', False) and hasattr(self, 'CardLogs') and self.CardLogs:
            cur_y = e.GetPosition(self).Y
            diff = self.log_start_y - cur_y
            new_h = max(40, min(450, self.log_start_h + diff))
            self.CardLogs.Height = new_h

    def on_split_log_up(self, sender, e):
        if getattr(self, 'is_resizing_log', False):
            self.is_resizing_log = False
            if hasattr(self, 'SplitLogs') and self.SplitLogs:
                self.SplitLogs.ReleaseMouseCapture()
            self.on_split_log_leave(sender, e)

    def log(self, text):
        try:
            if hasattr(self, 'TxtLog') and self.TxtLog:
                self.TxtLog.AppendText(str(text) + "\n")
                self.TxtLog.ScrollToEnd()
        except Exception:
            pass
        try:
            log_diag(str(text))
        except Exception:
            pass
        try:
            self.do_events()
        except Exception:
            pass

    def on_global_profile_changed(self, sender, e):
        for row in self.rows:
            if getattr(row, 'sheets_loaded', False) and getattr(row, 'sheet_rows', None):
                try:
                    row.on_options_changed(None, None)
                except Exception as ex:
                    log_diag("Profile change update error: " + str(ex))

    def update_file_count(self):
        total = len(self.rows)
        if total == 0:
            if hasattr(self, 'TxtFileCount') and self.TxtFileCount:
                self.TxtFileCount.Text = "0 Files Loaded"
            if hasattr(self, 'ChkSelectAllFiles') and self.ChkSelectAllFiles:
                self.ChkSelectAllFiles.IsChecked = False
            return
            
        selected = sum(1 for r in self.rows if getattr(r, 'chk_all', None) and r.chk_all.IsChecked != False)
        if hasattr(self, 'TxtFileCount') and self.TxtFileCount:
            self.TxtFileCount.Text = "{} Files Loaded ({} Selected)".format(total, selected)
            
        if hasattr(self, 'ChkSelectAllFiles') and self.ChkSelectAllFiles:
            all_checked = all(getattr(r, 'chk_all', None) and r.chk_all.IsChecked == True for r in self.rows)
            none_checked = all(getattr(r, 'chk_all', None) and r.chk_all.IsChecked == False for r in self.rows)
            if all_checked:
                self.ChkSelectAllFiles.IsChecked = True
            elif none_checked:
                self.ChkSelectAllFiles.IsChecked = False
            else:
                self.ChkSelectAllFiles.IsChecked = None

    def HeaderFileCell_MouseDown(self, sender, e):
        try:
            if hasattr(e, "OriginalSource") and isinstance(e.OriginalSource, System.Windows.Controls.CheckBox):
                return
            new_val = not (self.ChkSelectAllFiles.IsChecked == True)
            self.ChkSelectAllFiles.IsChecked = new_val
            self.ChkSelectAllFiles_Click(self.ChkSelectAllFiles, None)
            e.Handled = True
        except Exception:
            pass

    def ChkSelectAllFiles_Click(self, sender, e):
        val = (self.ChkSelectAllFiles.IsChecked == True)
        self.ChkSelectAllFiles.IsChecked = val
        for r in self.rows:
            if hasattr(r, 'chk_all') and r.chk_all:
                r.chk_all.IsChecked = val
            for cg in getattr(r, 'collection_groups', []):
                cg.set_checked_state(val)
            for sr in getattr(r, 'sheet_rows', []):
                sr.chk.IsChecked = val
        self.update_file_count()

    def get_cached_document(self, file_path):
        key = os.path.abspath(file_path).lower()
        if key in self.doc_cache:
            d, should_close = self.doc_cache[key]
            if d and getattr(d, 'IsValidObject', True):
                return (d, should_close)
        doc, should_close = get_or_open_document(file_path, close_worksets=False)
        self.doc_cache[key] = (doc, should_close)
        return (doc, should_close)

    def cleanup_cached_documents(self):
        for key, (d, should_close) in list(self.doc_cache.items()):
            if should_close and d:
                try:
                    if getattr(d, 'IsValidObject', True):
                        d.Close(False)
                except Exception:
                    pass
        self.doc_cache.clear()

    def on_window_closing(self, sender, e):
        self._cancel_export = True
        self.cleanup_cached_documents()

    def on_window_closed(self, sender, e):
        self.cleanup_cached_documents()
        
    def do_events(self):
        Application.Current.Dispatcher.Invoke(System.Windows.Threading.DispatcherPriority.Background, System.Action(lambda: None))

    def TitleBar_MouseDown(self, sender, e):
        try:
            if hasattr(e, "ClickCount") and e.ClickCount == 2:
                self.toggle_maximize()
                return
            if e.ChangedButton == System.Windows.Input.MouseButton.Left:
                self.DragMove()
        except:
            pass

    def MaximizeBtn_Click(self, sender, e):
        self.toggle_maximize()

    def toggle_maximize(self):
        try:
            if self.WindowState == System.Windows.WindowState.Maximized:
                self.WindowState = System.Windows.WindowState.Normal
                if hasattr(self, 'BtnMaximize'):
                    self.BtnMaximize.Content = u"\u25A1"
            else:
                self.WindowState = System.Windows.WindowState.Maximized
                if hasattr(self, 'BtnMaximize'):
                    self.BtnMaximize.Content = u"\u29C9"
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

    def select_sheet_advanced(self, sheet_row, is_ctrl=False, is_shift=False):
        if not hasattr(self, 'selected_sheets'):
            self.selected_sheets = []
            
        all_sheet_rows = []
        for r in self.rows:
            all_sheet_rows.extend(getattr(r, 'sheet_rows', []))
            
        brush_main = self.FindResource("TextMain")
        brush_dim = self.FindResource("TextDim")
        
        theme = self.settings.get("theme", "Dark")
        if theme == "Dark":
            select_brush = SolidColorBrush(ColorConverter.ConvertFromString("#4F4210"))
            select_text = SolidColorBrush(ColorConverter.ConvertFromString("#FFFFFF"))
        else:
            select_brush = SolidColorBrush(ColorConverter.ConvertFromString("#FCE38A"))
            select_text = SolidColorBrush(ColorConverter.ConvertFromString("#111111"))
            
        if is_shift and sheet_row in all_sheet_rows:
            anchor = getattr(self, 'selection_anchor', None)
            if not anchor or anchor not in all_sheet_rows:
                anchor = self.selected_sheets[0] if self.selected_sheets else sheet_row
                
            idx1 = all_sheet_rows.index(anchor)
            idx2 = all_sheet_rows.index(sheet_row)
            start_i = min(idx1, idx2)
            end_i = max(idx1, idx2)
            new_selection = all_sheet_rows[start_i:end_i+1]
            for s in self.selected_sheets:
                s.unhighlight(brush_main, brush_dim)
            self.selected_sheets = new_selection
            for s in self.selected_sheets:
                s.highlight(select_brush, select_text)
        elif is_ctrl:
            self.selection_anchor = sheet_row
            if sheet_row in self.selected_sheets:
                sheet_row.unhighlight(brush_main, brush_dim)
                self.selected_sheets.remove(sheet_row)
            else:
                self.selected_sheets.append(sheet_row)
                sheet_row.highlight(select_brush, select_text)
        else:
            self.selection_anchor = sheet_row
            for s in self.selected_sheets:
                s.unhighlight(brush_main, brush_dim)
            self.selected_sheets = [sheet_row]
            sheet_row.highlight(select_brush, select_text)
            
        self.selected_sheet = sheet_row
        self.update_sheet_details(sheet_row)

    def select_sheet(self, sheet_row):
        self.select_sheet_advanced(sheet_row, is_ctrl=False, is_shift=False)

    def update_sheet_details(self, sheet_row):
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
                    self.TxtPreviewHint.Text = "Ready to preview"
                if hasattr(self, 'BtnDoPreview'):
                    self.BtnDoPreview.Visibility = System.Windows.Visibility.Visible
        except Exception:
            pass

    def select_model_row_advanced(self, model_row, is_ctrl=False, is_shift=False):
        if not hasattr(self, 'selected_model_rows'):
            self.selected_model_rows = []
            
        all_models = list(self.rows)
        brush_main = self.FindResource("TextMain")
        brush_dim = self.FindResource("TextDim")
        
        theme = self.settings.get("theme", "Dark")
        if theme == "Dark":
            select_brush = SolidColorBrush(ColorConverter.ConvertFromString("#1E293B"))
            select_text = SolidColorBrush(ColorConverter.ConvertFromString("#38BDF8"))
        else:
            select_brush = SolidColorBrush(ColorConverter.ConvertFromString("#DBEAFE"))
            select_text = SolidColorBrush(ColorConverter.ConvertFromString("#1D4ED8"))

        # Clear sheet selection if any
        if hasattr(self, 'selected_sheets') and self.selected_sheets:
            for s in self.selected_sheets:
                s.unhighlight(brush_main, brush_dim)
            self.selected_sheets = []
            self.selected_sheet = None

        if is_shift and model_row in all_models:
            anchor = getattr(self, 'model_selection_anchor', None)
            if not anchor or anchor not in all_models:
                anchor = self.selected_model_rows[0] if self.selected_model_rows else model_row
                
            idx1 = all_models.index(anchor)
            idx2 = all_models.index(model_row)
            start_i = min(idx1, idx2)
            end_i = max(idx1, idx2)
            new_selection = all_models[start_i:end_i+1]
            for r in self.selected_model_rows:
                r.unhighlight(brush_main, brush_dim)
            self.selected_model_rows = new_selection
            for r in self.selected_model_rows:
                r.highlight(select_brush, select_text)
        elif is_ctrl:
            self.model_selection_anchor = model_row
            if model_row in self.selected_model_rows:
                model_row.unhighlight(brush_main, brush_dim)
                self.selected_model_rows.remove(model_row)
            else:
                self.selected_model_rows.append(model_row)
                model_row.highlight(select_brush, select_text)
        else:
            self.model_selection_anchor = model_row
            for r in self.selected_model_rows:
                r.unhighlight(brush_main, brush_dim)
            self.selected_model_rows = [model_row]
            model_row.highlight(select_brush, select_text)
            
        self.selected_model_row = model_row
        self.update_model_details(model_row)

    def update_model_details(self, model_row):
        try:
            status_text = model_row.txt_status.Text or "Ready"
            if hasattr(self, 'TxtDetailNumber'):
                self.TxtDetailNumber.Text = status_text
            if hasattr(self, 'TxtDetailName'):
                self.TxtDetailName.Text = os.path.basename(model_row.file_path)
            if hasattr(self, 'TxtDetailCollection'):
                self.TxtDetailCollection.Text = model_row.get_sheet_set_name() or "PRINT"
            if hasattr(self, 'TxtDetailExportName'):
                loc = model_row.output_location or ""
                self.TxtDetailExportName.Text = os.path.basename(loc) or loc or "-"
            if hasattr(self, 'TxtDetailModel'):
                self.TxtDetailModel.Text = model_row.file_path

            # Hide previous sheet image and show ready prompt
            if hasattr(self, 'ImgPreview') and self.ImgPreview:
                self.ImgPreview.Source = None
                self.ImgPreview.Visibility = System.Windows.Visibility.Collapsed
            if hasattr(self, 'GridPreviewLoading'):
                self.GridPreviewLoading.Visibility = System.Windows.Visibility.Collapsed
            if hasattr(self, 'GridPreviewPrompt'):
                self.GridPreviewPrompt.Visibility = System.Windows.Visibility.Visible
            if hasattr(self, 'TxtPreviewHint'):
                self.TxtPreviewHint.Text = "Click Preview Sheet to render cover page"
            if hasattr(self, 'BtnDoPreview'):
                self.BtnDoPreview.Visibility = System.Windows.Visibility.Visible
        except Exception as ex:
            log_diag("update_model_details error: " + str(ex))

    def Window_PreviewKeyDown(self, sender, e):
        try:
            import System.Windows.Input
            import System.Windows.Controls
            
            # 1. Escape: Close window only if no child/preview window or menu is active
            if e.Key == System.Windows.Input.Key.Escape:
                if hasattr(self, 'MenuSelectionOptions') and self.MenuSelectionOptions and self.MenuSelectionOptions.IsOpen:
                    self.MenuSelectionOptions.IsOpen = False
                    e.Handled = True
                    return
                if hasattr(self, 'OwnedWindows'):
                    has_open_child = False
                    for ow in self.OwnedWindows:
                        if getattr(ow, 'IsVisible', False):
                            has_open_child = True
                            break
                    if has_open_child:
                        e.Handled = True
                        return
                self.CloseBtn_Click(sender, e)
                e.Handled = True
                return
                
            # 2. Enter: Run Batch Export
            if e.Key == System.Windows.Input.Key.Enter:
                src = getattr(e, "OriginalSource", None)
                if src and isinstance(src, System.Windows.Controls.TextBox):
                    return
                if hasattr(self, 'BtnExport') and self.BtnExport.IsEnabled:
                    self.BtnExport_Click(sender, e)
                    e.Handled = True
                    return
                    
            # 3. Spacebar: Toggle selection on all highlighted models or sheets
            if e.Key == System.Windows.Input.Key.Space:
                src = getattr(e, "OriginalSource", None)
                if src and isinstance(src, System.Windows.Controls.TextBox):
                    return
                self.toggle_selected_sheets_space()
                e.Handled = True
                return

            # 4. Arrow navigation across models
            if e.Key in (System.Windows.Input.Key.Up, System.Windows.Input.Key.Down):
                src = getattr(e, "OriginalSource", None)
                if src and isinstance(src, (System.Windows.Controls.TextBox, System.Windows.Controls.ComboBox)):
                    return
                all_models = list(self.rows)
                if all_models:
                    cur = getattr(self, 'selected_model_row', None)
                    idx = all_models.index(cur) if (cur and cur in all_models) else -1
                    if e.Key == System.Windows.Input.Key.Down:
                        new_idx = min(idx + 1, len(all_models) - 1)
                    else:
                        new_idx = max(idx - 1, 0)
                    target_row = all_models[new_idx]
                    self.select_model_row_advanced(target_row, is_ctrl=False, is_shift=False)
                    try:
                        target_row.row_border.BringIntoView()
                    except:
                        pass
                    e.Handled = True
                    return
        except Exception:
            pass

    def toggle_selected_sheets_space(self):
        try:
            selected_models = getattr(self, 'selected_model_rows', [])
            if selected_models:
                any_unchecked = any(not (m.chk_all.IsChecked == True) for m in selected_models)
                target = True if any_unchecked else False
                for m in selected_models:
                    m.chk_all.IsChecked = target
                    m.on_chk_all_clicked(None, None)
                self.update_file_count()
                return

            selected = getattr(self, 'selected_sheets', [])
            if not selected and getattr(self, 'selected_sheet', None):
                selected = [self.selected_sheet]
                
            if selected:
                any_unchecked = any(not (s.chk.IsChecked == True) for s in selected)
                target = True if any_unchecked else False
                for s in selected:
                    s.chk.IsChecked = target
                    if s.parent_group:
                        s.parent_group.update_collection_checkbox()
                    elif s.parent:
                        s.parent.update_master_checkbox()
                affected_parents = set(s.parent for s in selected if s.parent)
                for p in affected_parents:
                    p.update_master_checkbox()
                self.update_file_count()
        except Exception as ex:
            log_diag("toggle_selected_sheets_space error: " + str(ex))

    def preview_sheet_row(self, sheet_row):
        self.select_sheet_advanced(sheet_row, is_ctrl=False, is_shift=False)
        self.BtnPreview_Click(None, None)

    def BtnSelectionOptions_Click(self, sender, e):
        try:
            btn = self.BtnSelectionOptions
            if hasattr(btn, "ContextMenu") and btn.ContextMenu:
                btn.ContextMenu.PlacementTarget = btn
                btn.ContextMenu.Placement = System.Windows.Controls.Primitives.PlacementMode.Bottom
                btn.ContextMenu.IsOpen = True
        except Exception as ex:
            log_diag("Error opening selection menu: " + str(ex))

    def MenuCheckSelected_Click(self, sender, e):
        self.menu_check_selected(True)

    def MenuUncheckSelected_Click(self, sender, e):
        self.menu_check_selected(False)

    def MenuInvertSelected_Click(self, sender, e):
        self.menu_invert_selected()

    def MenuCheckAll_Click(self, sender, e):
        self.menu_set_all_sheets(True)

    def MenuUncheckAll_Click(self, sender, e):
        self.menu_set_all_sheets(False)

    def MenuExpandAll_Click(self, sender, e):
        for r in self.rows:
            r.expand()

    def MenuCollapseAll_Click(self, sender, e):
        for r in self.rows:
            r.collapse()

    def MenuExpandAllFolders_Click(self, sender, e):
        for fg in getattr(self, 'folder_groups', []):
            fg.expand()

    def MenuCollapseAllFolders_Click(self, sender, e):
        for fg in getattr(self, 'folder_groups', []):
            fg.collapse()

    def BtnOutgoingFolder_Click(self, sender, e):
        try:
            btn = self.BtnOutgoingFolder
            if hasattr(btn, "ContextMenu") and btn.ContextMenu:
                btn.ContextMenu.PlacementTarget = btn
                btn.ContextMenu.Placement = System.Windows.Controls.Primitives.PlacementMode.Bottom
                btn.ContextMenu.IsOpen = True
        except Exception as ex:
            log_diag("Error opening outgoing menu: " + str(ex))

    def get_replicated_output_dir(self, file_path, outgoing_root):
        if not outgoing_root:
            return os.path.dirname(os.path.abspath(file_path))
        file_dir = os.path.dirname(os.path.abspath(file_path))
        if self.base_scan_dir:
            try:
                base_norm = os.path.abspath(self.base_scan_dir)
                rel = os.path.relpath(file_dir, base_norm)
                if not rel.startswith(".."):
                    if rel == ".":
                        return os.path.normpath(outgoing_root)
                    return os.path.normpath(os.path.join(outgoing_root, rel))
            except Exception:
                pass
        return os.path.normpath(os.path.join(outgoing_root, os.path.basename(file_dir)))

    def set_outgoing_root_folder(self, outgoing_path):
        self.outgoing_root_dir = os.path.normpath(outgoing_path) if outgoing_path else None
        if self.outgoing_root_dir:
            folder_name = os.path.basename(self.outgoing_root_dir) or self.outgoing_root_dir
            disp_name = (folder_name[:12] + u"…") if len(folder_name) > 12 else folder_name
            if hasattr(self, 'BtnOutgoingFolder') and self.BtnOutgoingFolder:
                self.BtnOutgoingFolder.Content = u"📁 Out: " + disp_name + u" ▾"
                self.BtnOutgoingFolder.ToolTip = "Outgoing Root Folder:\n" + self.outgoing_root_dir
            for row in self.rows:
                target_dir = self.get_replicated_output_dir(row.file_path, self.outgoing_root_dir)
                row.set_output_location(target_dir)
            self.log("[OUTGOING] Root folder set to: {}".format(self.outgoing_root_dir))
            self.log("[OUTGOING] Replicated folder structure updated for {} model(s).".format(len(self.rows)))
        else:
            if hasattr(self, 'BtnOutgoingFolder') and self.BtnOutgoingFolder:
                self.BtnOutgoingFolder.Content = u"📁 Outgoing ▾"
                self.BtnOutgoingFolder.ToolTip = "Set target root folder for replicated exports"
            for row in self.rows:
                row.set_output_location(os.path.dirname(os.path.abspath(row.file_path)))
            self.log("[OUTGOING] Output locations reset to source model folders.")

    def MenuSetOutgoing_Click(self, sender, e):
        selected_path = pick_folder_dialog("Select Outgoing Root Folder", self.outgoing_root_dir)
        if selected_path and os.path.exists(selected_path):
            self.set_outgoing_root_folder(selected_path)

    def MenuResetOutgoing_Click(self, sender, e):
        self.set_outgoing_root_folder(None)

    def MenuOpenOutgoing_Click(self, sender, e):
        target = self.outgoing_root_dir
        if not target or not os.path.exists(target):
            if self.rows and self.rows[0].output_location:
                target = self.rows[0].output_location
        if target and os.path.exists(target):
            try:
                import System.Diagnostics
                System.Diagnostics.Process.Start("explorer.exe", target)
            except Exception as ex:
                forms.alert("Could not open folder: " + str(ex))
        else:
            forms.alert("No outgoing folder has been set or folder does not exist.", title="Folder Not Found")

    def menu_check_selected(self, target_state):
        selected_models = getattr(self, 'selected_model_rows', [])
        if selected_models:
            for m in selected_models:
                m.chk_all.IsChecked = target_state
                m.on_chk_all_clicked(None, None)
            self.update_file_count()
            return

        selected = getattr(self, 'selected_sheets', [])
        if not selected and self.selected_sheet:
            selected = [self.selected_sheet]
        for s in selected:
            s.chk.IsChecked = target_state
            if s.parent_group:
                s.parent_group.update_collection_checkbox()
            elif s.parent:
                s.parent.update_master_checkbox()
        affected_parents = set(s.parent for s in selected if s.parent)
        for p in affected_parents:
            p.update_master_checkbox()
        self.update_file_count()

    def menu_invert_selected(self):
        selected_models = getattr(self, 'selected_model_rows', [])
        if selected_models:
            for m in selected_models:
                new_val = not (m.chk_all.IsChecked == True)
                m.chk_all.IsChecked = new_val
                m.on_chk_all_clicked(None, None)
            self.update_file_count()
            return

        selected = getattr(self, 'selected_sheets', [])
        if not selected and self.selected_sheet:
            selected = [self.selected_sheet]
        for s in selected:
            s.chk.IsChecked = not (s.chk.IsChecked == True)
            if s.parent_group:
                s.parent_group.update_collection_checkbox()
            elif s.parent:
                s.parent.update_master_checkbox()
        affected_parents = set(s.parent for s in selected if s.parent)
        for p in affected_parents:
            p.update_master_checkbox()
        self.update_file_count()

    def menu_set_all_sheets(self, target_state):
        for r in self.rows:
            r.chk_all.IsChecked = target_state
            for s in getattr(r, 'sheet_rows', []):
                s.chk.IsChecked = target_state
                if s.parent_group:
                    s.parent_group.update_collection_checkbox()
                elif s.parent:
                    s.parent.update_master_checkbox()
            r.update_master_checkbox()
        for fg in getattr(self, 'folder_groups', []):
            fg.update_folder_checkbox()
        self.update_file_count()

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
        cache_key = None
        title = "Sheet Preview"
        if self.selected_sheet:
            model_path = os.path.abspath(self.selected_sheet.parent.file_path).lower()
            sheet_id = self.selected_sheet.mock_sheet.UniqueId
            cache_key = (model_path, sheet_id)
            title = self.selected_sheet.generated_name or (self.selected_sheet.mock_sheet.SheetNumber + " - " + self.selected_sheet.mock_sheet.Name)
        elif getattr(self, 'selected_model_row', None):
            mr = self.selected_model_row
            file_path_abs = os.path.abspath(mr.file_path).lower()
            for k, p in self.preview_cache.items():
                if k[0] == file_path_abs:
                    cache_key = k
                    title = os.path.basename(mr.file_path)
                    break
        if cache_key and cache_key in self.preview_cache:
            img_path = self.preview_cache[cache_key]
            if os.path.exists(img_path):
                from _preview_script import show_preview
                show_preview(img_path, title, owner=self)

    def BtnPreview_Click(self, sender, e):
        if not self.selected_sheet and not getattr(self, 'selected_model_row', None):
            forms.alert("Please select a model or sheet from the list first.", title="No Selection")
            return
            
        if not self.selected_sheet and getattr(self, 'selected_model_row', None):
            mr = self.selected_model_row
            file_path = mr.file_path
            file_path_abs = os.path.abspath(file_path).lower()
            
            if hasattr(self, 'BtnDoPreview'):
                self.BtnDoPreview.IsEnabled = False
            mr.set_status("Loading Preview...")
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
                all_s = DB.FilteredElementCollector(bg_doc).OfClass(DB.ViewSheet).ToElements()
                valid_sheets = [s for s in all_s if not getattr(s, 'IsPlaceholder', False)]
                valid_sheets = sorted(valid_sheets, key=lambda x: getattr(x, 'SheetNumber', ''))
                if not valid_sheets:
                    forms.alert("No valid sheets found in model.", title="Preview")
                    mr.set_status("Ready")
                    return
                sheet_element = valid_sheets[0]
                sheet_id = sheet_element.UniqueId
                cache_key = (file_path_abs, sheet_id)
                if cache_key in self.preview_cache and os.path.exists(self.preview_cache[cache_key]):
                    self.display_preview_image(self.preview_cache[cache_key])
                    mr.set_status("Ready")
                    return
                    
                temp_dir = os.path.join(tempfile.gettempdir(), "RiyanPreview")
                if not os.path.exists(temp_dir):
                    try: os.makedirs(temp_dir)
                    except: pass
                img_prefix = "prev_" + str(abs(hash(cache_key)))
                img_path = os.path.join(temp_dir, img_prefix + ".png")
                
                img_opt = DB.ImageExportOptions()
                img_opt.ZoomType = DB.ZoomFitType.FitToPage
                img_opt.PixelSize = 1200
                img_opt.FilePath = img_path
                img_opt.FitDirection = DB.FitDirectionType.Horizontal
                img_opt.HLRandWFViewsFileType = DB.ImageFileType.PNG
                img_opt.ShadowViewsFileType = DB.ImageFileType.PNG
                img_opt.ExportRange = DB.ExportRange.SetOfViews
                
                from System.Collections.Generic import List
                v_list = List[DB.ElementId]()
                v_list.Add(sheet_element.Id)
                img_opt.SetViewsAndSheets(v_list)
                
                bg_doc.ExportImage(img_opt)
                
                actual_img = img_path
                if not os.path.exists(actual_img):
                    actual_img = os.path.join(temp_dir, img_prefix + " - Sheet - " + (sheet_element.SheetNumber or "") + " - " + (sheet_element.Name or "") + ".png")
                if not os.path.exists(actual_img):
                    for f in os.listdir(temp_dir):
                        if f.startswith(img_prefix) and f.endswith(".png"):
                            actual_img = os.path.join(temp_dir, f)
                            break
                if os.path.exists(actual_img):
                    self.preview_cache[cache_key] = actual_img
                    self.display_preview_image(actual_img)
                mr.set_status("Ready")
            except Exception as ex_prev:
                log_diag("Model preview error: " + str(ex_prev))
                mr.set_status("Ready")
            finally:
                if hasattr(self, 'BtnDoPreview'):
                    self.BtnDoPreview.IsEnabled = True
                if hasattr(self, 'GridPreviewLoading'):
                    self.GridPreviewLoading.Visibility = System.Windows.Visibility.Collapsed
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

            # Use Ultra-High Definition Presentation Raster (600 DPI)
            if hasattr(pdf_opt, "AlwaysUseRaster"):
                pdf_opt.AlwaysUseRaster = True

            if hasattr(DB, "RasterQualityType") and hasattr(pdf_opt, "RasterQuality"):
                pdf_opt.RasterQuality = getattr(DB.RasterQualityType, "Presentation", DB.RasterQualityType.High)

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
            
        set_keys = [k for k in sorted(row.sets_dict.keys()) if k.startswith("[Set]")]
        # If Sheet Sets exist in this document, ONLY show Sheet Sets in the dropdown
        if set_keys:
            ordered_keys = set_keys
        else:
            # Fallback if no Sheet Sets are configured in the model
            ordered_keys = ["<All Sheets>"]

        # Determine the default sheet set from collected sets without touching PrintManager (avoids DiRoots driver dialogs)
        default_idx = 0
        found_idx = -1

        # 1. Check for a set with "default" in the name
        for idx, k in enumerate(ordered_keys):
            if "default" in k.lower():
                found_idx = idx
                break

        # 2. Check for standard architectural sets (e.g. "arc set 1", "set 1", "arc set")
        if found_idx == -1:
            for kw in ["arc set 1", "set 1", "arc set", "set-1", "arc"]:
                for idx, k in enumerate(ordered_keys):
                    if kw in k.lower():
                        found_idx = idx
                        break
                if found_idx != -1:
                    break

        if found_idx != -1:
            default_idx = found_idx

        return ordered_keys, default_idx

    def determine_folder_group_name(self, file_path, base_dir=None):
        if not base_dir:
            base_dir = os.path.dirname(file_path)
        base_dir = os.path.abspath(base_dir)
        file_dir = os.path.abspath(os.path.dirname(file_path))
        rel = os.path.relpath(file_dir, base_dir)
        if rel == ".":
            return os.path.basename(base_dir) or "Project Models"
        parts = rel.split(os.sep)
        if len(parts) == 1:
            return os.path.basename(base_dir) or parts[0]
        else:
            group_parts = parts[:-1]
            if group_parts:
                return " \\ ".join(group_parts)
            return parts[0]

    def add_grouped_revit_files(self, file_paths, base_dir=None):
        self._cancel_export = False
        existing = set(os.path.abspath(r.file_path).lower() for r in self.rows)
        new_files = [f for f in file_paths if os.path.abspath(f).lower() not in existing]
        if not new_files:
            return

        default_set = "PRINT"
        if hasattr(self, 'CmbMasterSet') and self.CmbMasterSet:
            if self.CmbMasterSet.SelectedItem:
                default_set = str(self.CmbMasterSet.SelectedItem).strip()
            elif self.CmbMasterSet.Text:
                default_set = str(self.CmbMasterSet.Text).strip()
        elif hasattr(self, 'TxtMasterSet') and self.TxtMasterSet and self.TxtMasterSet.Text:
            default_set = self.TxtMasterSet.Text.strip() or "PRINT"

        from collections import OrderedDict
        groups_map = OrderedDict()
        for f in new_files:
            grp_name = self.determine_folder_group_name(f, base_dir)
            if grp_name not in groups_map:
                groups_map[grp_name] = []
            groups_map[grp_name].append(f)

        existing_groups = {fg.folder_name: fg for fg in getattr(self, 'folder_groups', [])}
        total_added = 0

        for grp_name, files_in_grp in groups_map.items():
            if grp_name in existing_groups:
                folder_group = existing_groups[grp_name]
            else:
                folder_group = FolderGroupRow(grp_name, self)
                if not hasattr(self, 'folder_groups'):
                    self.folder_groups = []
                self.folder_groups.append(folder_group)
                self.FileStack.Children.Add(folder_group.container)
                existing_groups[grp_name] = folder_group

            for f in files_in_grp:
                row = FileRow(f, self)
                row.set_sheet_set_name(default_set)
                if self.outgoing_root_dir:
                    row.set_output_location(self.get_replicated_output_dir(f, self.outgoing_root_dir))
                self.rows.append(row)
                folder_group.add_file_row(row)
                row.set_status("Ready")
                total_added += 1

        self.log("Added {} model(s) across {} folder group(s).".format(total_added, len(groups_map)))
        self.update_file_count()
        self.do_events()
        try:
            self.Activate()
        except Exception:
            pass

    def add_revit_files(self, file_paths):
        base_dir = None
        if file_paths:
            try:
                base_dir = os.path.dirname(os.path.abspath(file_paths[0]))
                if not self.base_scan_dir:
                    self.base_scan_dir = base_dir
            except Exception:
                base_dir = None
        self.add_grouped_revit_files(file_paths, base_dir=base_dir)

    def BtnApplySetToAll_Click(self, sender, e):
        target_name = "PRINT"
        if hasattr(self, 'CmbMasterSet') and self.CmbMasterSet:
            if self.CmbMasterSet.SelectedItem:
                target_name = str(self.CmbMasterSet.SelectedItem).strip()
            elif self.CmbMasterSet.Text:
                target_name = str(self.CmbMasterSet.Text).strip()
        elif hasattr(self, 'TxtMasterSet') and self.TxtMasterSet and self.TxtMasterSet.Text:
            target_name = self.TxtMasterSet.Text.strip()
        if not target_name:
            target_name = "PRINT"
            
        for row in self.rows:
            row.set_sheet_set_name(target_name)

    def BtnAddFile_Click(self, sender, e):
        dlg = WinForms.OpenFileDialog()
        dlg.Filter = "Revit Files (*.rvt)|*.rvt"
        dlg.Multiselect = True
        if dlg.ShowDialog() == WinForms.DialogResult.OK:
            self.add_revit_files(dlg.FileNames)

    def BtnAddFolder_Click(self, sender, e):
        import re
        selected_dir = pick_folder_dialog("Select Folder Containing Revit Projects")
        if not selected_dir or not os.path.exists(selected_dir):
            return
                
        self.base_scan_dir = selected_dir
        self.log("Scanning folder: {}".format(selected_dir))

        archive_keywords = (
            "PREVIOUS", "PREVIOUSE", "ARCHIVE", "ARCHIVES",
            "OLD", "BACKUP", "BACKUPS", "_BACKUP", "_BACKUPS",
            "INCOMING", "INCOMMING", "00 INCOMING", "00 INCOMMING",
            "TEMP", "TMP", "TRASH", "OBSOLETE", "SUPERSEDED",
            "LINKS", "REFERENCE", "REFERENCES", "REVIT_TEMP"
        )
        date_pattern = re.compile(r'(\d{4}[.\-_]\d{2}[.\-_]\d{2}|\d{2}[.\-_]\d{2}[.\-_]\d{4})')

        def is_archive_dir(rel_p):
            norm = os.path.normpath(rel_p).upper()
            parts = norm.split(os.sep)
            for seg in parts:
                if any(kw in seg for kw in archive_keywords):
                    return True
                if date_pattern.search(seg):
                    return True
            return False

        discovered = []
        try:
            for root, dirs, files in os.walk(selected_dir):
                rel_root = os.path.relpath(root, selected_dir)
                # Filter out archive/temp directories on the fly
                dirs[:] = [d for d in dirs if not any(kw in d.upper() for kw in archive_keywords) and not date_pattern.search(d)]
                if rel_root != "." and is_archive_dir(rel_root):
                    continue

                for f in files:
                    if not f.lower().endswith(".rvt") or f.startswith("~") or f.startswith("."):
                        continue
                    parts = f.split(".")
                    if len(parts) >= 3 and parts[-2].isdigit():
                        continue
                    full_p = os.path.join(root, f)
                    if is_archive_dir(os.path.relpath(os.path.dirname(full_p), selected_dir)):
                        continue
                    discovered.append(full_p)
        except Exception as ex:
            self.log("Scan warning: {}".format(ex))

        if not discovered:
            self.log("No valid Revit (.rvt) files found in: {}".format(selected_dir))
            forms.alert("No Revit (.rvt) files found in the selected folder structure.", title="No Files Found")
            return

        # Group discovered files by their immediate containing folder (building folder)
        from collections import OrderedDict
        by_building = OrderedDict()
        for f_path in discovered:
            b_dir = os.path.dirname(f_path)
            if b_dir not in by_building:
                by_building[b_dir] = []
            by_building[b_dir].append(f_path)

        active_models = []
        for b_dir, m_list in by_building.items():
            if len(m_list) == 1:
                active_models.append(m_list[0])
            else:
                m_list.sort(key=lambda p: os.path.getmtime(p) if os.path.exists(p) else 0, reverse=True)
                active_models.append(m_list[0])

        active_models.sort()
        self.log("Identified {} active Revit model(s) across {} folder(s).".format(len(active_models), len(by_building)))
        self.add_grouped_revit_files(active_models, base_dir=selected_dir)

    def BtnClearAll_Click(self, sender, e):
        self.cleanup_cached_documents()
        self.FileStack.Children.Clear()
        self.rows = []
        self.folder_groups = []
        self.base_scan_dir = None
        self.selected_sheet = None
        self.selected_model_rows = []
        self.selected_model_row = None
        self.model_selection_anchor = None
        self.preview_cache.clear()
        self.update_file_count()
        self.log("All files cleared.")
        if hasattr(self, 'ImgPreview') and self.ImgPreview:
            self.ImgPreview.Source = None
            self.ImgPreview.Visibility = System.Windows.Visibility.Collapsed
        if hasattr(self, 'GridPreviewPrompt') and self.GridPreviewPrompt:
            self.GridPreviewPrompt.Visibility = System.Windows.Visibility.Visible
        if hasattr(self, 'TxtPreviewHint') and self.TxtPreviewHint:
            self.TxtPreviewHint.Text = "Ready to preview"
        if hasattr(self, 'BtnDoPreview') and self.BtnDoPreview:
            self.BtnDoPreview.Visibility = System.Windows.Visibility.Visible
        for attr in ['TxtDetailNumber', 'TxtDetailName', 'TxtDetailCollection', 'TxtDetailExportName', 'TxtDetailModel']:
            if hasattr(self, attr):
                getattr(self, attr).Text = "-"

    def BtnExport_Click(self, sender, e):
        if not self.rows: return
        
        selected_rows = [r for r in self.rows if getattr(r, 'chk_all', None) and r.chk_all.IsChecked != False]
        if not selected_rows:
            forms.alert("No files selected for export. Please select at least one file.", title="None Selected")
            return

        for row in selected_rows:
            if not row.output_location or row.output_location == "Select Folder...":
                forms.alert("Please select output locations for all selected files.", title="Missing Location")
                return
        
        self.BtnExport.IsEnabled = False
        self._cancel_export = False
        self.Topmost = True
        try:
            self.Activate()
        except:
            pass
        is_check_print = self.RbCheckPrint.IsChecked
        
        self.log("Starting batch export for {} selected model(s)... Mode: {}".format(
            len(selected_rows), "Check Print (Combined PDF)" if is_check_print else "Final Export (Combined PDF + Separate CAD/PDF)"
        ))

        first_folder = None
        total_exported_sheets = 0
        total_failed_sheets = 0
        total_skipped_sheets = 0

        total_files = len(self.rows)
        total_selected = len(selected_rows)
        selected_processed = 0
        for idx, row in enumerate(self.rows):
            if self._cancel_export:
                self.log("Export canceled by user.")
                break
            
            if getattr(row, 'chk_all', None) and row.chk_all.IsChecked == False:
                row.set_status("Skipped")
                continue

            selected_processed += 1
            if hasattr(self, 'TxtFileCount') and self.TxtFileCount:
                self.TxtFileCount.Text = "Exporting [{}/{}] (File {} of {})...".format(
                    selected_processed, total_selected, idx + 1, total_files
                )
            
            self.log("[{}/{} Selected | Item {}/{}] Processing: {} (Set: {})".format(
                selected_processed, total_selected, idx + 1, total_files, os.path.basename(row.file_path), row.get_sheet_set_name()
            ))
            row.main_container.BringIntoView()
            self.do_events()
            
            if not first_folder and row.output_location:
                first_folder = row.output_location

            row.set_status("Preparing...")
            bg_doc = None
            should_close = False
            try:
                bg_doc, should_close = self.get_cached_document(row.file_path)
                try:
                    self.Activate()
                except:
                    pass
                
                em_script.doc = bg_doc
                
                pdf_items = []
                if row.sheet_rows:
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
                else:
                    target_set_name = row.get_sheet_set_name()
                    clean_target = target_set_name.replace("[Set] ", "").strip().lower()
                    
                    vss_collector = DB.FilteredElementCollector(bg_doc).OfClass(DB.ViewSheetSet).ToElements()
                    matched_vss = None
                    
                    # 1. Exact match
                    for vss in vss_collector:
                        if vss.Name.strip().lower() == clean_target:
                            matched_vss = vss
                            break
                    # 2. Substring match
                    if not matched_vss:
                        for vss in vss_collector:
                            if clean_target in vss.Name.strip().lower():
                                matched_vss = vss
                                break
                    # 3. Standard print/submission keywords if target was default 'print'
                    if not matched_vss and clean_target in ("print", "print set", "submission"):
                        for kw in ["submission", "submi", "arc set 1", "arc set", "set 1", "set-1", "tender", "print", "dwg", "arc"]:
                            for vss in vss_collector:
                                if kw in vss.Name.strip().lower():
                                    matched_vss = vss
                                    break
                            if matched_vss:
                                break
                    # 4. If only 1 ViewSheetSet exists in this document, use it!
                    if not matched_vss and len(vss_collector) == 1:
                        matched_vss = vss_collector[0]
                    # 5. If multiple ViewSheetSets exist, pick the one that has the most DrawingSheets
                    if not matched_vss and len(vss_collector) > 1:
                        best_vss = None
                        max_cnt = 0
                        for vss in vss_collector:
                            cnt = sum(1 for v in vss.Views if v.ViewType == DB.ViewType.DrawingSheet)
                            if cnt > max_cnt:
                                max_cnt = cnt
                                best_vss = vss
                        if best_vss and max_cnt > 0:
                            matched_vss = best_vss
                        
                    sheet_elements = []
                    set_label = ""
                    if matched_vss:
                        set_label = matched_vss.Name
                        for v in matched_vss.Views:
                            if v.ViewType == DB.ViewType.DrawingSheet:
                                try:
                                    if not getattr(v, 'IsPlaceholder', False):
                                        sheet_elements.append(v)
                                except:
                                    sheet_elements.append(v)
                    
                    # 6. Fallback: If no ViewSheetSet or set was empty, export ALL valid sheets!
                    if not sheet_elements:
                        all_s = DB.FilteredElementCollector(bg_doc).OfClass(DB.ViewSheet).ToElements()
                        for s in all_s:
                            try:
                                if getattr(s, 'IsPlaceholder', False):
                                    continue
                            except:
                                pass
                            s_name = (getattr(s, 'Name', '') or '').upper()
                            s_num = (getattr(s, 'SheetNumber', '') or '').upper()
                            if any(k in s_name or k in s_num for k in ("START-UP", "STARTUP", "START UP", "SPLASH")):
                                continue
                            sheet_elements.append(s)
                        set_label = "<All Valid Sheets>"
                    
                    self.log("[{}/{}] Model: {} -> Exporting {} sheets ({})".format(
                        idx + 1, total_files, os.path.basename(row.file_path), len(sheet_elements), set_label
                    ))
                            
                    sheet_elements = sorted(sheet_elements, key=lambda x: getattr(x, 'SheetNumber', ''))
                    
                    profile_name = None
                    if hasattr(self, 'CmbGlobalProfile') and self.CmbGlobalProfile and self.CmbGlobalProfile.SelectedItem:
                        profile_name = str(self.CmbGlobalProfile.SelectedItem)
                    elif hasattr(row, 'cmb_profile') and row.cmb_profile and row.cmb_profile.SelectedItem:
                        profile_name = str(row.cmb_profile.SelectedItem)
                    if not profile_name and self.profiles:
                        profile_name = self.profiles[0]
                    scheme_parts = self.settings.get("schemes", {}).get(profile_name, [])
                    if not scheme_parts:
                        scheme_parts = self.settings.get("combined_schemes", {}).get(profile_name, [])
                        
                    for sh in sheet_elements:
                        fname = em_script.generate_filename(sh, scheme_parts, bg_doc)
                        pdf_items.append({
                            "sheet": sh,
                            "filename": fname,
                            "ui_row": None
                        })
                
                if not pdf_items:
                    row.set_status("Skipped (No sheets)")
                    total_skipped_sheets += 1
                    if should_close:
                        try: bg_doc.Close(False)
                        except: pass
                    continue
                
                row.set_status("Exporting...", is_exporting=True)
                
                comb_name = None
                profile_name = None
                if hasattr(self, 'CmbGlobalProfile') and self.CmbGlobalProfile and self.CmbGlobalProfile.SelectedItem:
                    profile_name = str(self.CmbGlobalProfile.SelectedItem)
                elif hasattr(row, 'cmb_profile') and row.cmb_profile and row.cmb_profile.SelectedItem:
                    profile_name = str(row.cmb_profile.SelectedItem)
                if not profile_name and self.profiles:
                    profile_name = self.profiles[0]
                comb_parts = None
                if profile_name:
                    comb_parts = self.settings.get("combined_schemes", {}).get(profile_name, None)
                    if not comb_parts:
                        comb_parts = self.settings.get("schemes", {}).get(profile_name, None)
                
                if comb_parts and pdf_items:
                    try:
                        first_sheet = pdf_items[0]["sheet"]
                        comb_name = em_script.generate_filename(first_sheet, comb_parts, bg_doc)
                    except Exception as ex_name:
                        log_diag("Combined naming error: " + str(ex_name))
                        comb_name = None
                
                if not comb_name or comb_name.strip() in ["", "Combined_PDF"]:
                    comb_name = os.path.splitext(os.path.basename(row.file_path))[0]
                
                comb_filename = comb_name.strip() + ".pdf"
                
                # Selective archiving: safely move ONLY previous deliverables matching this model
                if row.output_location:
                    if not os.path.exists(row.output_location):
                        try:
                            os.makedirs(row.output_location)
                        except Exception as ex_m:
                            log_diag("Makedirs error: " + str(ex_m))
                    target_files = [comb_filename, comb_name.strip() + " - LIST OF DRAWINGS.doc", comb_name.strip() + " - LIST OF DRAWINGS.xlsx"]
                    if not is_check_print:
                        for itm in pdf_items:
                            f_base = itm.get("filename", "")
                            if f_base:
                                target_files.append(f_base + ".pdf")
                                target_files.append(f_base + ".dwg")
                    try:
                        em_script.archive_previous_exports(row.output_location, target_files)
                    except Exception as ex_arch:
                        log_diag("Selective archive error: " + str(ex_arch))
                
                # Auto-sync Cover Page Sheet Issue Date with standard sheet issue date
                try:
                    std_issue_date = None
                    for itm in pdf_items:
                        sh = itm.get("sheet")
                        sn = (sh.Name or "").upper().strip()
                        snum = (sh.SheetNumber or "").upper().strip()
                        if "COVER" not in sn and "COVER" not in snum and "00-000-000-00" not in snum and "000-000-00" not in snum and not any(k in sn or k in snum for k in ("START-UP", "STARTUP", "START UP", "SPLASH")):
                            p_d = sh.get_Parameter(DB.BuiltInParameter.SHEET_ISSUE_DATE)
                            if p_d and p_d.HasValue and p_d.AsString():
                                val = p_d.AsString().strip()
                                if val:
                                    std_issue_date = val
                                    break
                    if std_issue_date:
                        for itm in pdf_items:
                            sh = itm.get("sheet")
                            sn = (sh.Name or "").upper().strip()
                            snum = (sh.SheetNumber or "").upper().strip()
                            if "COVER" in sn or "COVER" in snum:
                                p_d = sh.get_Parameter(DB.BuiltInParameter.SHEET_ISSUE_DATE)
                                cur_val = p_d.AsString().strip() if (p_d and p_d.HasValue and p_d.AsString()) else ""
                                if p_d and not p_d.IsReadOnly and cur_val != std_issue_date:
                                    t_date = DB.Transaction(bg_doc, "Auto Sync Cover Page Issue Date")
                                    t_date.Start()
                                    p_d.Set(std_issue_date)
                                    tb_collector = DB.FilteredElementCollector(bg_doc, sh.Id).OfCategory(DB.BuiltInCategory.OST_TitleBlocks).OfClass(DB.FamilyInstance).ToElements()
                                    for tb_inst in tb_collector:
                                        for d_name in ("ISSUED DATE", "Sheet Issue Date", "Issue Date", "Date/Time Stamp"):
                                            p_tb_d = tb_inst.LookupParameter(d_name)
                                            if p_tb_d and not p_tb_d.IsReadOnly:
                                                p_tb_d.Set(std_issue_date)
                                    t_date.Commit()
                                    bg_doc.Regenerate()
                                    log_diag("Synced Cover Page Issue Date to '{}'".format(std_issue_date))
                except Exception as ex_sync_date:
                    log_diag("Cover Page date sync warning: " + str(ex_sync_date))

                # Wire ui_row so Revit ProgressChanged events directly update each sheet row
                mock_queue = [MockQueueItem(item["sheet"], item["filename"], ui_row=item["ui_row"]) for item in pdf_items]
                
                # Ensure all selected sheets explicitly start as Pending
                for item in pdf_items:
                    if item.get("ui_row"):
                        item["ui_row"].set_status("Pending")
                self.do_events()

                if is_check_print:
                    # Check Print Mode: Combined PDF only
                    self.TxtPercent.Text = "Exporting Combined PDF..."
                    self.ExportProgressBar.Value = 0
                    self.do_events()
                    
                    em_script.export_combined_pdf_2022(row.output_location, mock_queue, comb_filename, get_zoom_fit_type(), 100, window_instance=self)
                    
                    for item in pdf_items:
                        if item.get("ui_row"):
                            item["ui_row"].set_status("Done", is_done=True)
                    total_exported_sheets += len(pdf_items)
                else:
                    # Final Export Mode: Individual Single PDFs and DWGs first!
                    # Each sheet transitions Pending -> Exporting... -> Done individually
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
                        s_row = item.get("ui_row")
                        sheet = item["sheet"]
                        fname = item["filename"]
                        
                        # Active sheet is Exporting... (all previous are Done, all upcoming are Pending!)
                        if s_row:
                            s_row.set_status("Exporting...", is_exporting=True)
                        pct = int((float(idx) / total_single) * 90)
                        self.ExportProgressBar.Value = pct
                        self.TxtPercent.Text = "Exporting [{}/{}]: {} (PDF)".format(idx + 1, total_single, fname)
                        self.do_events()
                        
                        try:
                            em_script.export_pdf_2022(pdf_out_dir, sheet, fname, get_zoom_fit_type(), 100)
                        except Exception as ex_pdf:
                            log_diag("Single PDF error: " + str(ex_pdf))
                            
                        self.TxtPercent.Text = "Exporting [{}/{}]: {} (DWG)".format(idx + 1, total_single, fname)
                        self.do_events()
                        
                        try:
                            em_script.export_dwg(dwg_out_dir, sheet, fname, None)
                        except Exception as ex_dwg:
                            log_diag("DWG error: " + str(ex_dwg))
                            
                        # Mark this sheet as Done!
                        if s_row:
                            s_row.set_status("Done", is_done=True)
                        total_exported_sheets += 1
                        self.do_events()

                    # Now that all individual sheets are Done, generate Combined PDF
                    if not self._cancel_export:
                        self.TxtPercent.Text = "Generating Combined PDF ({} sheets)...".format(len(pdf_items))
                        self.ExportProgressBar.Value = 95
                        self.do_events()
                        em_script.export_combined_pdf_2022(row.output_location, mock_queue, comb_filename, get_zoom_fit_type(), 100, window_instance=self)

                # Generate Excel / Word Transmittal / Drawing List
                if not self._cancel_export and (not hasattr(self, 'ChkDrawingList') or self.ChkDrawingList.IsChecked == True):
                    try:
                        list_fmt = "Word" if (getattr(self, 'RbBatchListWord', None) and self.RbBatchListWord.IsChecked == True) else "Excel"
                        self.TxtPercent.Text = "Generating {} Drawing List...".format(list_fmt)
                        self.do_events()
                        vms = [item.SheetVM for item in mock_queue]
                        em_script.generate_excel_transmittal(row.output_location, vms, bg_doc, comb_name.strip(), comb_parts, format_type=list_fmt)
                    except Exception as ex_tr:
                        log_diag("Drawing list note: " + str(ex_tr))
                
                if should_close and bg_doc:
                    try:
                        bg_doc.Close(False)
                    except:
                        pass
                    bg_doc = None
                
                # Evict from doc cache to free RAM immediately
                file_key = os.path.abspath(row.file_path).lower()
                self.doc_cache.pop(file_key, None)
                try:
                    import System
                    System.GC.Collect()
                    System.GC.WaitForPendingFinalizers()
                except Exception:
                    pass
                
                row.set_status("Done", is_done=True)
                
            except Exception as ex:
                total_failed_sheets += len(row.sheet_rows)
                row.set_status("Error", is_error=True)
                if should_close and bg_doc:
                    try:
                        bg_doc.Close(False)
                    except:
                        pass
                    bg_doc = None
                file_key = os.path.abspath(row.file_path).lower()
                self.doc_cache.pop(file_key, None)
                try:
                    import System
                    System.GC.Collect()
                    System.GC.WaitForPendingFinalizers()
                except Exception:
                    pass
                log_diag("Export error: " + str(ex) + "\n" + traceback.format_exc())
                
        self.Topmost = False
        self.BtnExport.IsEnabled = True
        self.ExportProgressBar.Value = 100
        self.TxtPercent.Text = "Finished!"
        self.update_file_count()
        
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
                
            self.log("Batch export finished! Total exported: {}, Failed: {}, Skipped: {}.".format(
                total_exported_sheets, total_failed_sheets, total_skipped_sheets
            ))

            try:
                cw = em_script.CustomExportCompletedWindow(first_folder, msg, theme)
                if hasattr(cw, 'win') and cw.win:
                    cw.win.Topmost = True
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
        try:
            form.ShowDialog()
        finally:
            form.cleanup_cached_documents()
    except Exception as ex:
        forms.alert('Failed to load UI:\n\n' + str(ex) + '\n\n' + traceback.format_exc(), title='UI Error')

main()