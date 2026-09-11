import os
import clr
clr.AddReference("System")
import System
from pyrevit import forms
from System.Windows.Media.Imaging import BitmapImage

class PreviewForm(forms.WPFWindow):
    def __init__(self, xaml_file_name, img_path, title, doc=None, view_id=None):
        forms.WPFWindow.__init__(self, xaml_file_name)
        self.TxtTitle.Text = "Previewing: " + title
        self.doc = doc
        self.view_id = view_id
        self.preview_ctrl = None
        self.Closed += self.on_closed

        if img_path and os.path.exists(img_path):
            try:
                bmp = BitmapImage()
                bmp.BeginInit()
                bmp.UriSource = System.Uri(img_path, System.UriKind.Absolute)
                bmp.CacheOption = System.Windows.Media.Imaging.BitmapCacheOption.OnLoad
                bmp.EndInit()
                
                self.ImgPreview.Source = bmp
                self.ImgPreview.Stretch = getattr(System.Windows.Media.Stretch, "None")
                try:
                    System.Windows.Media.RenderOptions.SetBitmapScalingMode(self.ImgPreview, System.Windows.Media.BitmapScalingMode.HighQuality)
                except Exception:
                    pass
            except Exception:
                pass
        
        self.ScrollViewerMain.PreviewMouseWheel += self.on_mouse_wheel
        self.ScrollViewerMain.PreviewMouseLeftButtonDown += self.on_pan_start
        self.ScrollViewerMain.PreviewMouseMove += self.on_pan_move
        self.ScrollViewerMain.PreviewMouseLeftButtonUp += self.on_pan_end
        self.ScrollViewerMain.MouseLeave += self.on_pan_end
        self.Loaded += self.on_loaded
        
        self.is_panning = False
        self.pan_start_pos = None
        self.h_start_offset = 0
        self.v_start_offset = 0

    def on_loaded(self, sender, e):
        if self.doc and self.view_id:
            try:
                from Autodesk.Revit.UI import PreviewControl
                self.preview_ctrl = PreviewControl(self.doc, self.view_id)
                if hasattr(self, 'BorderVectorPreviewHost') and self.BorderVectorPreviewHost:
                    self.BorderVectorPreviewHost.Child = self.preview_ctrl
                    self.BorderVectorPreviewHost.Visibility = System.Windows.Visibility.Visible
                if hasattr(self, 'ScrollViewerMain') and self.ScrollViewerMain:
                    self.ScrollViewerMain.Visibility = System.Windows.Visibility.Collapsed
                if hasattr(self, 'BorderBottomBar') and self.BorderBottomBar:
                    self.BorderBottomBar.Visibility = System.Windows.Visibility.Collapsed
                return
            except Exception as ex:
                import traceback
                print("PreviewControl vector initialization error:\n{}".format(traceback.format_exc()))
        if hasattr(self, 'BorderVectorPreviewHost') and self.BorderVectorPreviewHost:
            self.BorderVectorPreviewHost.Visibility = System.Windows.Visibility.Collapsed
        if hasattr(self, 'ScrollViewerMain') and self.ScrollViewerMain:
            self.ScrollViewerMain.Visibility = System.Windows.Visibility.Visible
        if hasattr(self, 'BorderBottomBar') and self.BorderBottomBar:
            self.BorderBottomBar.Visibility = System.Windows.Visibility.Visible
        self.BtnFit_Click(None, None)

    def on_closed(self, sender, e):
        try:
            if self.preview_ctrl:
                self.preview_ctrl.Dispose()
                self.preview_ctrl = None
        except Exception:
            pass

    def BtnClose_Click(self, sender, e):
        self.Close()
        
    def TitleBar_MouseDown(self, sender, e):
        if e.ClickCount == 2:
            self.toggle_maximize()
            return
        if e.ChangedButton == System.Windows.Input.MouseButton.Left:
            self.DragMove()

    def BtnMaximize_Click(self, sender, e):
        self.toggle_maximize()

    def toggle_maximize(self):
        if self.WindowState == System.Windows.WindowState.Maximized:
            self.WindowState = System.Windows.WindowState.Normal
            if hasattr(self, 'BtnMaximize'):
                self.BtnMaximize.Content = u"\u25A2"
        else:
            self.WindowState = System.Windows.WindowState.Maximized
            if hasattr(self, 'BtnMaximize'):
                self.BtnMaximize.Content = u"\u29C9"
        self.Dispatcher.BeginInvoke(System.Action(lambda: self.BtnFit_Click(None, None)))

    def on_pan_start(self, sender, e):
        # Don't pan if clicking the scrollbars
        original_source = e.OriginalSource
        source_type = original_source.GetType().Name
        if "Thumb" in source_type or "RepeatButton" in source_type or "ScrollBar" in source_type:
            return
            
        self.is_panning = True
        self.pan_start_pos = e.GetPosition(self.ScrollViewerMain)
        self.h_start_offset = self.ScrollViewerMain.HorizontalOffset
        self.v_start_offset = self.ScrollViewerMain.VerticalOffset
        self.ScrollViewerMain.CaptureMouse()
        self.ScrollViewerMain.Cursor = System.Windows.Input.Cursors.SizeAll

    def on_pan_move(self, sender, e):
        if self.is_panning:
            current_pos = e.GetPosition(self.ScrollViewerMain)
            delta_x = current_pos.X - self.pan_start_pos.X
            delta_y = current_pos.Y - self.pan_start_pos.Y
            
            self.ScrollViewerMain.ScrollToHorizontalOffset(self.h_start_offset - delta_x)
            self.ScrollViewerMain.ScrollToVerticalOffset(self.v_start_offset - delta_y)

    def on_pan_end(self, sender, e):
        if self.is_panning:
            self.is_panning = False
            self.ScrollViewerMain.ReleaseMouseCapture()
            self.ScrollViewerMain.Cursor = System.Windows.Input.Cursors.Arrow

    def on_mouse_wheel(self, sender, e):
        e.Handled = True
        
        sv = self.ScrollViewerMain
        mouse_pos_sv = e.GetPosition(sv)
        
        h_off = sv.HorizontalOffset
        v_off = sv.VerticalOffset
        
        old_scale = self.SliderZoom.Value
        
        delta = e.Delta
        step = 0.15 if delta > 0 else -0.15
        new_scale = old_scale + step
        
        if new_scale < self.SliderZoom.Minimum: new_scale = self.SliderZoom.Minimum
        if new_scale > self.SliderZoom.Maximum: new_scale = self.SliderZoom.Maximum
        
        if new_scale == old_scale: return
        
        self.SliderZoom.Value = new_scale
        sv.UpdateLayout()
        
        ratio = new_scale / old_scale
        new_h_off = (h_off + mouse_pos_sv.X) * ratio - mouse_pos_sv.X
        new_v_off = (v_off + mouse_pos_sv.Y) * ratio - mouse_pos_sv.Y
        
        sv.ScrollToHorizontalOffset(new_h_off)
        sv.ScrollToVerticalOffset(new_v_off)

    def SliderZoom_ValueChanged(self, sender, e):
        try:
            self.ImgScale.ScaleX = self.SliderZoom.Value
            self.ImgScale.ScaleY = self.SliderZoom.Value
        except:
            pass

    def BtnFit_Click(self, sender, e):
        try:
            vw = self.ScrollViewerMain.ViewportWidth
            vh = self.ScrollViewerMain.ViewportHeight
            iw = self.ImgPreview.Source.PixelWidth
            ih = self.ImgPreview.Source.PixelHeight
            
            if iw > 0 and ih > 0:
                scale_x = vw / iw
                scale_y = vh / ih
                fit_scale = min(scale_x, scale_y) * 0.95
                if fit_scale < self.SliderZoom.Minimum: self.SliderZoom.Minimum = fit_scale
                self.SliderZoom.Value = fit_scale
        except:
            pass
            
    def BtnActual_Click(self, sender, e):
        self.SliderZoom.Value = 1.0

def show_preview(img_path=None, title="", doc=None, view_id=None):
    xaml_path = os.path.join(os.path.dirname(__file__), 'Preview.xaml')
    form = PreviewForm(xaml_path, img_path, title, doc=doc, view_id=view_id)
    form.ShowDialog()