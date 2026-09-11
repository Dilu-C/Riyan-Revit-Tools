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
            self.TxtMessage.Text = "Riyan Revit Tools V{} has been installed successfully!\n\nYou can view the new features now or reload pyRevit to start using them.".format(version_info if version_info else "2.0")
            self.BtnCancel.Visibility = System.Windows.Visibility.Visible
            self.BtnCancel.Content = "What's New 🚀"
            self.BtnCancel.Width = 120
            self.BtnAction.Content = "Reload pyRevit"
            self.BtnAction.Width = 120
            
    def BtnAction_Click(self, sender, e):
        self.result = "RELOAD"
        self.Close()
        
    def BtnCancel_Click(self, sender, e):
        self.result = "WHATS_NEW"
        self.Close()
        
    def TitleBar_MouseDown(self, sender, e):
        try:
            self.DragMove()
        except:
            pass
            
    def CloseBtn_Click(self, sender, e):
        self.result = "RELOAD"
        self.Close()

def show_dialog(state, info=None):
    xaml_file = os.path.join(os.path.dirname(__file__), "UI.xaml")
    w = UpdateForm(xaml_file, state, info)
    w.ShowDialog()
    return w.result

def update_tools():
    try:
        # 1. Determine paths
        curr = os.path.dirname(__file__)
        extension_dir = None
        for _ in range(6):
            if os.path.basename(curr).endswith(".extension") or os.path.exists(os.path.join(curr, "startup.py")):
                extension_dir = curr
                break
            curr = os.path.dirname(curr)
        if not extension_dir:
            extension_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        parent_dir = os.path.dirname(extension_dir)
        
        # Check both potential locations for version.txt
        v_candidates = [
            os.path.join(extension_dir, 'version.txt'),
            os.path.join(parent_dir, 'version.txt')
        ]
        
        # 2. Get local version
        local_version = "2.0"
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
                source_ext = os.path.join(source_dir, "Riyan.extension")
                
                def sync_clean_tree(src, dst):
                    if not os.path.exists(dst):
                        os.makedirs(dst)
                    src_items = set(os.listdir(src))
                    dst_items = set(os.listdir(dst))
                    
                    # Automatically remove obsolete files/folders that exist locally but not in GitHub
                    for old_item in (dst_items - src_items):
                        if old_item in [".git", "__pycache__"]:
                            continue
                        target_path = os.path.join(dst, old_item)
                        try:
                            if os.path.isdir(target_path):
                                shutil.rmtree(target_path, ignore_errors=True)
                            else:
                                os.remove(target_path)
                        except Exception:
                            pass
                            
                    # Copy and update all files from source
                    for item in src_items:
                        s = os.path.join(src, item)
                        d = os.path.join(dst, item)
                        if os.path.isdir(s):
                            sync_clean_tree(s, d)
                        else:
                            shutil.copy2(s, d)
                            
                if os.path.basename(extension_dir).endswith(".extension") and os.path.exists(source_ext):
                    sync_clean_tree(source_ext, extension_dir)
                    # Also update version.txt in parent directory if it exists
                    src_v = os.path.join(source_dir, "version.txt")
                    if os.path.exists(src_v) and os.path.exists(parent_dir):
                        try:
                            shutil.copy2(src_v, os.path.join(parent_dir, "version.txt"))
                        except Exception:
                            pass
                else:
                    sync_clean_tree(source_dir, extension_dir)

                # Clean up legacy / unwanted files from pyRevit Extensions and user folders
                unwanted_files = [
                    "GEMINI.md", "GEMINI", "test_compile.py", "test_msg.py",
                    "Install_Riyan_Tools.bat", "Install_Riyan_Tools.zip"
                ]
                unwanted_dirs = [".agents"]
                
                ext_root = os.path.expandvars(r"%APPDATA%\pyRevit\Extensions")
                clean_targets = set(filter(None, [extension_dir, parent_dir, ext_root]))
                legacy_panel_items = ["Update.pushbutton", "Update.stack", "WhatsNew.pushbutton"]
                for folder in clean_targets:
                    if not os.path.exists(folder):
                        continue
                    for uf in unwanted_files:
                        target_f = os.path.join(folder, uf)
                        if os.path.isfile(target_f):
                            try:
                                os.remove(target_f)
                            except Exception:
                                pass
                    for ud in unwanted_dirs:
                        target_d = os.path.join(folder, ud)
                        if os.path.isdir(target_d):
                            try:
                                shutil.rmtree(target_d, ignore_errors=True)
                            except Exception:
                                pass
                    # Clean legacy button directories inside System.panel and Coordination.panel
                    try:
                        for root, dirs, files in os.walk(folder):
                            bname = os.path.basename(root)
                            if bname == "System.panel":
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
                            elif bname == "Coordination.panel":
                                for item in ["link.pushbutton"]:
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
                
                pb.update_progress(100, 100)
                
            # 9. Trigger pyRevit Reload & What's New
            choice = show_dialog("SUCCESS", online_version)
            if choice == "WHATS_NEW":
                try:
                    if extension_dir not in sys.path:
                        sys.path.insert(0, extension_dir)
                    import whats_new
                    try:
                        reload(whats_new)
                    except Exception:
                        pass
                    if hasattr(whats_new, "show_whats_new"):
                        whats_new.show_whats_new()
                except Exception as ex:
                    forms.alert("Could not open What's New window:\n" + str(ex), title="What's New")
            sessionmgr.reload_pyrevit()
            
    except Exception as e:
        show_dialog("ERROR", "An error occurred during the update: {}".format(str(e)))

if __name__ == '__main__':
    update_tools()
