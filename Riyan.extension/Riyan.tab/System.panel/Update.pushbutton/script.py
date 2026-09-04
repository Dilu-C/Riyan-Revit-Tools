# -*- coding: utf-8 -*-
import os
import urllib2
import zipfile
import tempfile
import shutil
import System
from pyrevit import forms
from pyrevit.loader import sessionmgr

class UpdateForm(forms.WPFWindow):
    def __init__(self, xaml_path, state, version_info=None):
        forms.WPFWindow.__init__(self, xaml_path)
        self.result = False
        
        if state == "UP_TO_DATE":
            self.TxtTitle.Text = "System Up to Date"
            self.TxtMessage.Text = "You are already on the latest version (V{}). No updates needed!".format(version_info)
            self.BtnCancel.Visibility = System.Windows.Visibility.Collapsed
            self.BtnAction.Content = "OK"
        elif state == "UPDATE_AVAILABLE":
            self.TxtTitle.Text = "Update Available!"
            self.TxtMessage.Text = "A new update (V{}) for the Riyan Revit Plugin Suite is available!\nCurrent version: V{}\n\nWould you like to download and install this update now?".format(version_info[0], version_info[1])
            self.BtnAction.Content = "Update Now"
        elif state == "ERROR":
            self.TxtTitle.Text = "Update Error"
            self.TxtMessage.Text = str(version_info)
            self.BtnCancel.Visibility = System.Windows.Visibility.Collapsed
            self.BtnAction.Content = "OK"
        elif state == "SUCCESS":
            self.TxtTitle.Text = "Update Complete"
            self.TxtMessage.Text = "Update installed successfully!\nRevit will now reload to apply the changes."
            self.BtnCancel.Visibility = System.Windows.Visibility.Collapsed
            self.BtnAction.Content = "Reload pyRevit"
            
    def BtnAction_Click(self, sender, e):
        self.result = True
        self.Close()
        
    def BtnCancel_Click(self, sender, e):
        self.result = False
        self.Close()
        
    def TitleBar_MouseDown(self, sender, e):
        try:
            self.DragMove()
        except:
            pass
            
    def CloseBtn_Click(self, sender, e):
        self.result = False
        self.Close()

def show_dialog(state, info=None):
    xaml_file = os.path.join(os.path.dirname(__file__), "UI.xaml")
    w = UpdateForm(xaml_file, state, info)
    w.ShowDialog()
    return w.result

def update_tools():
    try:
        # 1. Determine paths
        extension_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        parent_dir = os.path.dirname(extension_dir)
        
        # Check both potential locations for version.txt
        v_candidates = [
            os.path.join(extension_dir, 'version.txt'),
            os.path.join(parent_dir, 'version.txt')
        ]
        
        # 2. Get local version
        local_version = "1.3"
        for vfile in v_candidates:
            if os.path.exists(vfile):
                try:
                    with open(vfile, 'r') as f:
                        val = f.read().strip()
                        if val:
                            local_version = val
                            break
                except:
                    pass
                
        # 3. Check online version
        import time
        url_version = "https://raw.githubusercontent.com/Dilu-C/Riyan-Revit-Tools/main/version.txt?t=" + str(time.time())
        req = urllib2.Request(url_version)
        req.add_header('Cache-Control', 'no-cache')
        req.add_header('Pragma', 'no-cache')
        try:
            response = urllib2.urlopen(req, timeout=5)
            online_version = response.read().strip()
        except:
            show_dialog("ERROR", "Could not connect to GitHub to check for updates. Please check your internet connection.")
            return
            
        # 4. Compare versions
        if online_version == local_version:
            show_dialog("UP_TO_DATE", local_version)
            return
            
        # 5. Prompt for update
        if show_dialog("UPDATE_AVAILABLE", (online_version, local_version)):
            with forms.ProgressBar(title="Downloading Update...") as pb:
                pb.update_progress(10, 100)
                
                # 6. Download ZIP
                zip_url = "https://github.com/Dilu-C/Riyan-Revit-Tools/archive/refs/heads/main.zip"
                temp_dir = tempfile.gettempdir()
                zip_path = os.path.join(temp_dir, "Riyan_Update.zip")
                
                req_zip = urllib2.Request(zip_url)
                req_zip.add_header('Cache-Control', 'no-cache')
                with open(zip_path, 'wb') as f:
                    f.write(urllib2.urlopen(req_zip).read())
                    
                pb.update_progress(50, 100)
                pb.title = "Installing Update..."
                
                # 7. Extract ZIP to a temporary folder
                extract_path = os.path.join(temp_dir, "Riyan_Extracted")
                if os.path.exists(extract_path):
                    shutil.rmtree(extract_path, ignore_errors=True)
                os.makedirs(extract_path)
                
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_path)
                    
                pb.update_progress(80, 100)
                
                # 8. Copy contents over the active extension directory
                source_dir = os.path.join(extract_path, "Riyan-Revit-Tools-main")
                
                def copy_tree_overwrite(src, dst):
                    if not os.path.exists(dst):
                        os.makedirs(dst)
                    for item in os.listdir(src):
                        s = os.path.join(src, item)
                        d = os.path.join(dst, item)
                        if os.path.isdir(s):
                            copy_tree_overwrite(s, d)
                        else:
                            shutil.copy2(s, d)
                            
                copy_tree_overwrite(source_dir, extension_dir)
                
                pb.update_progress(100, 100)
                
            # 9. Trigger pyRevit Reload
            if show_dialog("SUCCESS"):
                sessionmgr.reload_pyrevit()
            
    except Exception as e:
        show_dialog("ERROR", "An error occurred during the update: {}".format(str(e)))

if __name__ == '__main__':
    update_tools()
