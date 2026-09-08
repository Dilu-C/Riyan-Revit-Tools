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

def get_or_open_document(file_path, close_worksets=False):
    """
    Safely gets an already open document or opens it in background.
    Returns: (doc, should_close)
    Prevents 'The active document may not be closed from the API' error.
    """
    import re
    file_path_abs = os.path.abspath(file_path).lower()
    file_base = os.path.splitext(os.path.basename(file_path))[0].lower()
    clean_fb = re.sub(r'[^a-zA-Z0-9]', '', file_base)
    
    # 0. Check revit.doc directly
    try:
        curr_doc = getattr(revit, "doc", None)
        if curr_doc:
            p = curr_doc.PathName
            if p and os.path.abspath(p).lower() == file_path_abs:
                return (curr_doc, False)
            t = curr_doc.Title.lower()
            clean_t = re.sub(r'[^a-zA-Z0-9]', '', t)
            if t == file_base or t.startswith(file_base) or file_base.startswith(t) or (clean_fb and clean_t and (clean_fb in clean_t or clean_t in clean_fb)):
                return (curr_doc, False)
    except Exception:
        pass

    # 1. Check ActiveUIDocument
    active_uidoc = getattr(__revit__, "ActiveUIDocument", None)
    if active_uidoc and active_uidoc.Document:
        try:
            doc = active_uidoc.Document
            p = doc.PathName
            if p and os.path.abspath(p).lower() == file_path_abs:
                return (doc, False)
            t = doc.Title.lower()
            clean_t = re.sub(r'[^a-zA-Z0-9]', '', t)
            if t == file_base or t.startswith(file_base) or file_base.startswith(t) or (clean_fb and clean_t and (clean_fb in clean_t or clean_t in clean_fb)):
                return (doc, False)
        except Exception:
            pass
            
    # 2. Check all open documents
    for d in app.Documents:
        try:
            p = d.PathName
            if p and os.path.abspath(p).lower() == file_path_abs:
                return (d, False)
            t = d.Title.lower()
            clean_t = re.sub(r'[^a-zA-Z0-9]', '', t)
            if t == file_base or t.startswith(file_base) or file_base.startswith(t) or (clean_fb and clean_t and (clean_fb in clean_t or clean_t in clean_fb)):
                return (d, False)
        except Exception:
            pass
            
    # 3. Background open
    opt = DB.OpenOptions()
    opt.DetachFromCentralOption = DB.DetachFromCentralOption.DetachAndPreserveWorksets
    
    if close_worksets:
        try:
            ws_opt = DB.WorksetConfiguration(DB.WorksetConfigurationOption.CloseAllWorksets)
            opt.SetOpenWorksetsConfiguration(ws_opt)
        except Exception:
            pass
    else:
        try:
            ws_opt = DB.WorksetConfiguration(DB.WorksetConfigurationOption.OpenLastViewed)
            opt.SetOpenWorksetsConfiguration(ws_opt)
        except Exception:
            pass
            
    model_path = DB.ModelPathUtils.ConvertUserVisiblePathToModelPath(file_path)
    bg_doc = app.OpenDocumentFile(model_path, opt)
    
    # Reload Revit links if not closing worksets
    if not close_worksets:
        try:
            link_types = DB.FilteredElementCollector(bg_doc).OfClass(DB.RevitLinkType).ToElements()
            for lt in link_types:
                try:
                    if not lt.IsLoaded(bg_doc, lt.Id):
                        lt.Load()
                except Exception:
                    try:
                        lt.Reload()
                    except Exception:
                        pass
        except Exception:
            pass

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
    def __init__(self, sheet, target_filename):
        self.SheetId = sheet.UniqueId
        self.SheetNumber = getattr(sheet, 'SheetNumber', '')
        self.SheetName = getattr(sheet, 'Name', '')
        self.TargetFileName = target_filename
        self._status = ""
        
        class MockSheetVM:
            def __init__(self, s):
                self.Sheet = s
        self.SheetVM = MockSheetVM(sheet)
        
    @property
    def Status(self): return self._status
    @Status.setter
    def Status(self, value): self._status = value

# ----------------- UI CLASSES -----------------
class SheetRow:
    def __init__(self, mock_sheet, parent_file_row, form_instance):
        self.mock_sheet = mock_sheet
        self.parent = parent_file_row
        self.form = form_instance
        self.generated_name = ""
        
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
                    # Fallback if binding fails
                    fixed_widths = {0: 380, 1: 130, 2: 130, 3: 130, 4: 150} # 4 is * in XAML but we give it a min fallback
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
        self.chk.Margin = Thickness(30, 0, 5, 0)
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
        if brush_main: self.txt_status.Foreground = brush_dim
        Grid.SetColumn(self.txt_status, 8)
        self.grid.Children.Add(self.txt_status)
        
        self.border.MouseLeftButtonDown += self.on_select

    def on_select(self, sender, e):
        self.form.select_sheet(self)
        
    def set_status(self, msg, is_done=False, is_exporting=False, is_error=False):
        if is_done:
            self.txt_status.Text = "[Done] " + msg
        elif is_exporting:
            self.txt_status.Text = "[Exporting] " + msg
        elif is_error:
            self.txt_status.Text = "[Error] " + msg
        else:
            self.txt_status.Text = msg
        self.form.do_events()

class FileRow:
    def __init__(self, file_path, form_instance):
        self.file_path = file_path
        self.form = form_instance
        self.profiles = form_instance.profiles
        self.output_location = ""
        self.mock_doc = MockDoc()
        self.sets_dict = {}
        self.sheet_rows = []
        self.is_expanded = True
        
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
                    fixed_widths = {0: 380, 1: 130, 2: 130, 3: 130, 4: 150} # 4 is * in XAML but we give it a min fallback
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
        self.chk_all.VerticalAlignment = VerticalAlignment.Center
        self.chk_all.Margin = Thickness(5, 0, 5, 0)
        self.chk_all.Checked += self.on_chk_all_changed
        self.chk_all.Unchecked += self.on_chk_all_changed
        sp_file.Children.Add(self.chk_all)
        
        self.btn_expand = Button()
        self.btn_expand.Content = "-"
        self.btn_expand.Width = 20
        self.btn_expand.Height = 20
        self.btn_expand.Background = SolidColorBrush(System.Windows.Media.Colors.Transparent)
        self.btn_expand.BorderThickness = Thickness(0)
        self.btn_expand.Foreground = brush_dim
        self.btn_expand.Click += self.on_expand
        sp_file.Children.Add(self.btn_expand)
        
        sp_file.Cursor = System.Windows.Input.Cursors.Hand
        sp_file.MouseLeftButtonDown += self.on_expand
        
        self.txt_file = TextBlock()
        self.txt_file.Text = os.path.basename(file_path)
        self.txt_file.ToolTip = os.path.basename(file_path)
        self.txt_file.TextTrimming = System.Windows.TextTrimming.CharacterEllipsis
        sp_file.ClipToBounds = True
        self.txt_file.VerticalAlignment = VerticalAlignment.Center
        self.txt_file.Margin = Thickness(5,0,5,0)
        self.txt_file.ToolTip = file_path
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
        self.cmb_profile.ItemsSource = self.profiles
        self.cmb_profile.VerticalAlignment = VerticalAlignment.Center
        self.cmb_profile.Margin = Thickness(5,0,5,0)
        active_sc = form_instance.settings.get("active_scheme", "")
        if active_sc and active_sc in self.profiles:
            self.cmb_profile.SelectedItem = active_sc
        elif self.profiles:
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
        self.txt_status.Margin = Thickness(5,0,5,0)
        if brush_main: self.txt_status.Foreground = brush_main
        Grid.SetColumn(self.txt_status, 8)
        self.grid.Children.Add(self.txt_status)
        
        self.sheet_stack = StackPanel()
        self.main_container.Children.Add(self.sheet_stack)

    def on_chk_all_changed(self, sender, e):
        is_checked = self.chk_all.IsChecked
        for sr in self.sheet_rows:
            sr.chk.IsChecked = is_checked

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
        if is_done:
            self.txt_status.Text = "[Done] " + msg
        elif is_exporting:
            self.txt_status.Text = "[Exporting] " + msg
        elif is_error:
            self.txt_status.Text = "[Error] " + msg
        else:
            self.txt_status.Text = msg
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
            
            mock_sheets = self.sets_dict.get(set_name, [])
            for ms in mock_sheets:
                s_row = SheetRow(ms, self, self.form)
                name = em_script.generate_filename(ms, scheme_parts, self.mock_doc)
                s_row.generated_name = name
                s_row.txt_name.Text = name
                s_row.txt_name.ToolTip = name
                self.sheet_rows.append(s_row)
                self.sheet_stack.Children.Add(s_row.border)
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
        
    def do_events(self):
        Application.Current.Dispatcher.Invoke(System.Windows.Threading.DispatcherPriority.Background, System.Action(lambda: None))

    def TitleBar_MouseDown(self, sender, e):
        try:
            self.DragMove()
        except:
            pass

    def CloseBtn_Click(self, sender, e):
        self._cancel_export = True
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
            if hasattr(self, 'TxtDetailExportName'):
                self.TxtDetailExportName.Text = sheet_row.generated_name or '-'
            if hasattr(self, 'TxtDetailModel'):
                self.TxtDetailModel.Text = os.path.basename(sheet_row.parent.file_path)

            # Check cached preview
            sheet_id = ms.UniqueId
            if sheet_id in self.preview_cache and os.path.exists(self.preview_cache[sheet_id]):
                self.display_preview_image(self.preview_cache[sheet_id])
            else:
                if hasattr(self, 'ImgPreview'):
                    self.ImgPreview.Visibility = System.Windows.Visibility.Collapsed
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
            if hasattr(self, 'GridPreviewPrompt'):
                self.GridPreviewPrompt.Visibility = System.Windows.Visibility.Collapsed
            if hasattr(self, 'GridPreviewLoading'):
                self.GridPreviewLoading.Visibility = System.Windows.Visibility.Collapsed
        except Exception:
            pass

    def on_preview_image_click(self, sender, e):
        if self.selected_sheet and self.selected_sheet.mock_sheet.UniqueId in self.preview_cache:
            img_path = self.preview_cache[self.selected_sheet.mock_sheet.UniqueId]
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
        sheet_id = sr.mock_sheet.UniqueId
        
        sr.set_status("Loading Vector Preview...")
        if hasattr(self, 'GridPreviewLoading'):
            self.GridPreviewLoading.Visibility = System.Windows.Visibility.Visible
        if hasattr(self, 'GridPreviewPrompt'):
            self.GridPreviewPrompt.Visibility = System.Windows.Visibility.Collapsed
        if hasattr(self, 'ImgPreview'):
            self.ImgPreview.Visibility = System.Windows.Visibility.Collapsed
        self.do_events()
        
        bg_doc = None
        should_close = False
        try:
            bg_doc, should_close = get_or_open_document(file_path, close_worksets=False)
            
            sheet_element = bg_doc.GetElement(sheet_id)
            if not sheet_element:
                forms.alert("Sheet not found in document.")
                if should_close:
                    try: bg_doc.Close(False)
                    except: pass
                sr.set_status("")
                if hasattr(self, 'GridPreviewPrompt'):
                    self.GridPreviewPrompt.Visibility = System.Windows.Visibility.Visible
                if hasattr(self, 'GridPreviewLoading'):
                    self.GridPreviewLoading.Visibility = System.Windows.Visibility.Collapsed
                return

            temp_dir = os.environ.get("TEMP")
            pdf_prefix = "riyan_preview_" + sheet_element.UniqueId
            png_out = os.path.join(temp_dir, pdf_prefix + ".png")

            # 1. Clean up old temp preview files for this sheet
            try:
                for f in os.listdir(temp_dir):
                    if f.startswith(pdf_prefix):
                        try: os.remove(os.path.join(temp_dir, f))
                        except: pass
            except Exception:
                pass

            # 2. Export 1-sheet PDF using Revit's native vector engine (guarantees 100% full model geometry)
            pdf_opt = DB.PDFExportOptions()
            pdf_opt.FileName = pdf_prefix
            pdf_opt.Combine = True
            zt = get_zoom_fit_type()
            if zt is not None:
                pdf_opt.ZoomType = zt
            views = System.Collections.Generic.List[DB.ElementId]()
            views.Add(sheet_element.Id)
            
            export_ok = bg_doc.Export(temp_dir, views, pdf_opt)

            # Locate the exported PDF file
            actual_pdf = os.path.join(temp_dir, pdf_prefix + ".pdf")
            if not os.path.exists(actual_pdf):
                actual_pdf = None
                try:
                    for f in os.listdir(temp_dir):
                        if f.endswith(".pdf"):
                            if f.startswith(pdf_prefix) or (sheet_element.SheetNumber and sheet_element.SheetNumber in f):
                                actual_pdf = os.path.join(temp_dir, f)
                                break
                except Exception:
                    pass

            if not actual_pdf or not os.path.exists(actual_pdf):
                forms.alert("Failed to export PDF for preview.\n\nExport Status: {}\nOutput Path: {}\nSheet: {}".format(
                    export_ok, os.path.join(temp_dir, pdf_prefix + ".pdf"), getattr(sheet_element, 'SheetNumber', '-')))
                sr.set_status("Preview Error", is_error=True)
                if hasattr(self, 'GridPreviewPrompt'):
                    self.GridPreviewPrompt.Visibility = System.Windows.Visibility.Visible
                if hasattr(self, 'GridPreviewLoading'):
                    self.GridPreviewLoading.Visibility = System.Windows.Visibility.Collapsed
                return

            # 3. Convert page 0 of PDF to high-res PNG using native Windows WinRT
            ps1_path = os.path.join(os.path.dirname(__file__), "render_pdf.ps1")
            import subprocess
            cmd = ['powershell.exe', '-ExecutionPolicy', 'Bypass', '-WindowStyle', 'Hidden', '-File', ps1_path, '-PdfPath', actual_pdf, '-PngPath', png_out, '-Width', '2400']
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            proc = subprocess.Popen(cmd, startupinfo=startupinfo)
            proc.wait()

            sr.set_status("")

            if os.path.exists(png_out) and os.path.getsize(png_out) > 0:
                self.preview_cache[sheet_id] = png_out
                self.display_preview_image(png_out)
            else:
                # Direct fallback to system PDF viewer
                os.startfile(actual_pdf)
                sr.set_status("Opened in PDF Viewer")
                if hasattr(self, 'GridPreviewPrompt'):
                    self.GridPreviewPrompt.Visibility = System.Windows.Visibility.Visible
                if hasattr(self, 'GridPreviewLoading'):
                    self.GridPreviewLoading.Visibility = System.Windows.Visibility.Collapsed

        except Exception as ex:
            sr.set_status("Preview Error", is_error=True)
            if hasattr(self, 'GridPreviewPrompt'):
                self.GridPreviewPrompt.Visibility = System.Windows.Visibility.Visible
            if hasattr(self, 'GridPreviewLoading'):
                self.GridPreviewLoading.Visibility = System.Windows.Visibility.Collapsed
            forms.alert(str(ex))
        finally:
            if should_close and bg_doc:
                try: bg_doc.Close(False)
                except Exception: pass

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
                
        # 2. Add Sheet Sets
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
            row.sets_dict[vss.Name] = mock_list
            
        keys = sorted(row.sets_dict.keys())
        if "<All Sheets>" in keys:
            keys.remove("<All Sheets>")
            keys.insert(0, "<All Sheets>")
        return keys

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
                    bg_doc, should_close = get_or_open_document(row.file_path, close_worksets=True)
                    
                    sets = self.extract_mock_data(bg_doc, row)
                    
                    row.cmb_set.ItemsSource = sets
                    if sets:
                        row.cmb_set.SelectedIndex = 0
                        
                    if should_close:
                        try: bg_doc.Close(False)
                        except: pass
                    row.set_status("Ready")
                except Exception as ex:
                    row.set_status("Error loading sets: " + str(ex), is_error=True)
                    if should_close and bg_doc:
                        try: bg_doc.Close(False)
                        except: pass
                    forms.alert(str(ex) + '\n\n' + traceback.format_exc())

    def BtnClearAll_Click(self, sender, e):
        self.FileStack.Children.Clear()
        self.rows = []
        self.selected_sheet = None

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

        for row in self.rows:
            if self._cancel_export: break
            
            row.main_container.BringIntoView()
            self.do_events()
            
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

            row.set_status("Opening file...", is_exporting=True)
            bg_doc = None
            should_close = False
            try:
                bg_doc, should_close = get_or_open_document(row.file_path, close_worksets=False)
                
                em_script.doc = bg_doc
                
                pdf_items = []
                for s_row in row.sheet_rows:
                    if s_row.chk.IsChecked != True:
                        s_row.set_status("Skipped", is_done=True)
                        continue
                        
                    sheet_element = bg_doc.GetElement(s_row.mock_sheet.UniqueId)
                    if sheet_element:
                        pdf_items.append({
                            "sheet": sheet_element,
                            "filename": s_row.generated_name,
                            "ui_row": s_row
                        })
                        s_row.set_status("Waiting...", is_exporting=True)
                
                if not pdf_items:
                    row.set_status("No sheets to export", is_error=True)
                    if should_close:
                        try: bg_doc.Close(False)
                        except: pass
                    continue
                
                row.set_status("Exporting Combined PDF...", is_exporting=True)
                comb_filename = "Combined_Set_{}.pdf".format(os.path.basename(row.file_path).replace('.rvt',''))
                
                mock_queue = [MockQueueItem(item["sheet"], item["filename"]) for item in pdf_items]
                em_script.export_combined_pdf_2022(row.output_location, mock_queue, comb_filename, get_zoom_fit_type(), 100, window_instance=self)
                
                for item in pdf_items:
                    item["ui_row"].set_status("Combined Check Print Done", is_done=True)
                
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

                    for item in pdf_items:
                        if self._cancel_export: break
                        s_row = item["ui_row"]
                        sheet = item["sheet"]
                        fname = item["filename"]
                        
                        s_row.set_status("Exporting PDF...", is_exporting=True)
                        self.TxtPercent.Text = "Exporting: {}".format(fname)
                        self.do_events()
                        em_script.export_pdf_2022(pdf_out_dir, sheet, fname, get_zoom_fit_type(), 100)
                        
                        s_row.set_status("Exporting CAD...", is_exporting=True)
                        em_script.export_dwg(dwg_out_dir, sheet, fname, None)
                        
                        s_row.set_status("Done", is_done=True)
                
                if should_close:
                    try: bg_doc.Close(False)
                    except: pass
                row.set_status("Completed!", is_done=True)
                
            except Exception as ex:
                row.set_status("Error", is_error=True)
                if should_close and bg_doc:
                    try: bg_doc.Close(False)
                    except: pass
                
        self.BtnExport.IsEnabled = True
        self.TxtPercent.Text = "Finished!"

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