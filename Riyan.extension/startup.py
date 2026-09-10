# -*- coding: utf-8 -*-
import os
import sys
import threading
import time

def get_versions():
    current_dir = os.path.dirname(__file__)
    extension_dir = os.path.dirname(current_dir)
    parent_dir = os.path.dirname(extension_dir)
    
    candidates = [
        os.path.join(current_dir, 'version.txt'),
        os.path.join(extension_dir, 'version.txt'),
        os.path.join(parent_dir, 'version.txt')
    ]
    
    local_version = "1.3"
    for c in candidates:
        if os.path.exists(c):
            try:
                with open(c, 'r') as f:
                    v = f.read().strip()
                    if v:
                        local_version = v
                        break
            except Exception:
                pass

    try:
        try:
            import urllib2
        except ImportError:
            import urllib.request as urllib2
            
        url = "https://raw.githubusercontent.com/Dilu-C/Riyan-Revit-Tools/main/version.txt?t=" + str(int(time.time()))
        req = urllib2.Request(url)
        req.add_header('Cache-Control', 'no-cache')
        req.add_header('Pragma', 'no-cache')
        
        response = urllib2.urlopen(req, timeout=8)
        raw_val = response.read()
        if hasattr(raw_val, 'decode'):
            raw_val = raw_val.decode('utf-8')
        online_version = raw_val.strip()
    except Exception:
        online_version = None

    return local_version, online_version

def show_update_toast(online_version, local_version):
    try:
        import clr
        clr.AddReference('PresentationFramework')
        clr.AddReference('PresentationCore')
        clr.AddReference('WindowsBase')
        import System
        from System.Windows import Application, Window, WindowStyle, SystemParameters, WindowStartupLocation
        from System.Windows.Controls import Border, StackPanel, TextBlock, Button, Grid, ColumnDefinition
        from System.Windows.Media import Brushes, Color, SolidColorBrush
        from System.Windows.Threading import DispatcherTimer
        from System import TimeSpan

        def build_and_show():
            win = Window()
            win.Title = "Riyan Tools Update"
            win.WindowStyle = WindowStyle.None
            win.AllowsTransparency = True
            win.Background = Brushes.Transparent
            win.Topmost = True
            win.ShowInTaskbar = False
            win.Width = 380
            win.Height = 125
            win.WindowStartupLocation = WindowStartupLocation.Manual
            
            # Position at bottom right corner above Windows taskbar
            work_area = SystemParameters.WorkArea
            win.Left = work_area.Right - win.Width - 20
            win.Top = work_area.Bottom - win.Height - 20
            
            border = Border()
            border.CornerRadius = System.Windows.CornerRadius(10)
            border.Background = SolidColorBrush(Color.FromRgb(32, 32, 35))
            border.BorderBrush = SolidColorBrush(Color.FromRgb(128, 47, 45)) # Signature Riyan Maroon
            border.BorderThickness = System.Windows.Thickness(2)
            border.Padding = System.Windows.Thickness(14)
            
            grid = Grid()
            col1 = ColumnDefinition()
            col1.Width = System.Windows.GridLength(1, System.Windows.GridUnitType.Star)
            col2 = ColumnDefinition()
            col2.Width = System.Windows.GridLength(25)
            grid.ColumnDefinitions.Add(col1)
            grid.ColumnDefinitions.Add(col2)
            
            stack = StackPanel()
            
            # Header
            txt_title = TextBlock()
            txt_title.Text = u"🚀 Riyan Tools Update Available!"
            txt_title.Foreground = SolidColorBrush(Color.FromRgb(245, 245, 245))
            txt_title.FontWeight = System.Windows.FontWeights.Bold
            txt_title.FontSize = 13
            stack.Children.Add(txt_title)
            
            # Message
            txt_msg = TextBlock()
            txt_msg.Text = u"New Version V{} is available (Current: V{}).\nGo to Riyan tab > System > Update to install.".format(online_version, local_version)
            txt_msg.Foreground = SolidColorBrush(Color.FromRgb(175, 175, 180))
            txt_msg.FontSize = 11
            txt_msg.Margin = System.Windows.Thickness(0, 4, 0, 10)
            stack.Children.Add(txt_msg)
            
            # Buttons
            btn_panel = StackPanel()
            btn_panel.Orientation = System.Windows.Controls.Orientation.Horizontal
            
            btn_update = Button()
            btn_update.Content = u"Got It 👍"
            btn_update.Background = SolidColorBrush(Color.FromRgb(128, 47, 45))
            btn_update.Foreground = Brushes.White
            btn_update.FontWeight = System.Windows.FontWeights.SemiBold
            btn_update.FontSize = 11
            btn_update.Padding = System.Windows.Thickness(16, 4, 16, 4)
            btn_update.BorderThickness = System.Windows.Thickness(0)
            btn_update.Cursor = System.Windows.Input.Cursors.Hand
            btn_update.Click += lambda s, e: win.Close()
            btn_panel.Children.Add(btn_update)
            
            stack.Children.Add(btn_panel)
            Grid.SetColumn(stack, 0)
            grid.Children.Add(stack)
            
            # Close button
            btn_close = Button()
            btn_close.Content = u"✕"
            btn_close.Background = Brushes.Transparent
            btn_close.Foreground = SolidColorBrush(Color.FromRgb(140, 140, 140))
            btn_close.BorderThickness = System.Windows.Thickness(0)
            btn_close.FontSize = 12
            btn_close.Cursor = System.Windows.Input.Cursors.Hand
            btn_close.VerticalAlignment = System.Windows.VerticalAlignment.Top
            btn_close.Click += lambda s, e: win.Close()
            Grid.SetColumn(btn_close, 1)
            grid.Children.Add(btn_close)
            
            border.Child = grid
            win.Content = border
            
            # Auto-close timer (25 seconds)
            timer = DispatcherTimer()
            timer.Interval = TimeSpan.FromSeconds(25)
            def on_tick(s, e):
                timer.Stop()
                try:
                    win.Close()
                except:
                    pass
            timer.Tick += on_tick
            timer.Start()
            
            win.Show()

        if Application.Current:
            Application.Current.Dispatcher.Invoke(System.Action(build_and_show))
        else:
            build_and_show()
            
    except Exception as e:
        try:
            import clr
            clr.AddReference("System.Windows.Forms")
            from System.Windows.Forms import MessageBox, MessageBoxButtons, MessageBoxIcon, MessageBoxOptions, MessageBoxDefaultButton
            msg = "A new update (V{}) for Riyan Revit Tools is available!\nPlease click the 'Update' button in the Riyan tab.".format(online_version)
            MessageBox.Show(msg, "Riyan Tools Update", MessageBoxButtons.OK, MessageBoxIcon.Information, MessageBoxDefaultButton.Button1, MessageBoxOptions.ServiceNotification)
        except:
            pass

def cleanup_legacy_files():
    try:
        import shutil
        current_dir = os.path.dirname(__file__)
        parent_dir = os.path.dirname(current_dir)
        ext_folder = os.path.expandvars(r"%APPDATA%\pyRevit\Extensions")
        
        target_folders = set(filter(None, [ext_folder, parent_dir, current_dir]))
        bad_files = [
            "GEMINI.md", "GEMINI", "test_compile.py", "test_msg.py",
            "Install_Riyan_Tools.bat", "Install_Riyan_Tools.zip"
        ]
        bad_dirs = [".agents"]
        
        legacy_panel_items = ["Update.pushbutton", "Update.stack", "WhatsNew.pushbutton"]
        
        for folder in target_folders:
            if not os.path.exists(folder):
                continue
            for f in bad_files:
                p = os.path.join(folder, f)
                if os.path.isfile(p):
                    try:
                        os.remove(p)
                    except Exception:
                        pass
            for d in bad_dirs:
                p = os.path.join(folder, d)
                if os.path.isdir(p):
                    try:
                        shutil.rmtree(p, ignore_errors=True)
                    except Exception:
                        pass
            # Clean legacy button directories inside System.panel
            try:
                for root, dirs, files in os.walk(folder):
                    if os.path.basename(root) == "System.panel":
                        for item in legacy_panel_items:
                            target = os.path.join(root, item)
                            if os.path.exists(target):
                                try:
                                    if os.path.isdir(target):
                                        shutil.rmtree(target, ignore_errors=True)
                                    else:
                                        os.remove(target)
                                except Exception:
                                    pass
            except Exception:
                pass
    except Exception:
        pass

def check_for_updates():
    try:
        cleanup_legacy_files()
        # Give Revit time to load UI
        time.sleep(12)
        local_v, online_v = get_versions()
        
        # If newer update available -> Show desktop side toast only
        if online_v and online_v != local_v:
            show_update_toast(online_v, local_v)
            return
    except Exception:
        pass

# Run in daemon background thread
t = threading.Thread(target=check_for_updates)
t.isDaemon = True
t.start()


