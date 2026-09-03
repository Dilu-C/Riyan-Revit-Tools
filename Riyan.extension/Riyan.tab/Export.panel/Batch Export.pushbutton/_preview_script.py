import os
from pyrevit import forms
import System
from System.Windows.Media.Imaging import BitmapImage
from System import Uri, UriKind

class PreviewForm(forms.WPFWindow):
    def __init__(self, xaml_file_name, img_path, title):
        forms.WPFWindow.__init__(self, xaml_file_name)
        self.TxtTitle.Text = "Previewing: " + title
        
        bmp = BitmapImage()
        bmp.BeginInit()
        bmp.UriSource = Uri(img_path, UriKind.Absolute)
        bmp.CacheOption = System.Windows.Media.Imaging.BitmapCacheOption.OnLoad
        bmp.EndInit()
        
        self.ImgPreview.Source = bmp
        self.ImgPreview.Stretch = System.Windows.Media.Stretch.None
        
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
        self.BtnFit_Click(None, None)

    def BtnClose_Click(self, sender, e):
        self.Close()
        
    def TitleBar_MouseDown(self, sender, e):
        if e.ChangedButton == System.Windows.Input.MouseButton.Left:
            self.DragMove()

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

def show_preview(img_path, title):
    xaml_path = os.path.join(os.path.dirname(__file__), 'Preview.xaml')
    form = PreviewForm(xaml_path, img_path, title)
    form.ShowDialog()