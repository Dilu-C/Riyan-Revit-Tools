import os
import urllib2
import threading
import time
from pyrevit import forms

def check_for_updates():
    try:
        # Give Revit time to fully load UI
        time.sleep(15)
        
        extension_dir = os.path.dirname(os.path.dirname(__file__))
        parent_dir = os.path.dirname(extension_dir)
        v_candidates = [
            os.path.join(extension_dir, 'version.txt'),
            os.path.join(parent_dir, 'version.txt')
        ]
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
                
        # Fetch online version directly from GitHub raw content
        url = "https://raw.githubusercontent.com/Dilu-C/Riyan-Revit-Tools/main/version.txt?t=" + str(time.time())
        req = urllib2.Request(url)
        # Prevent caching
        req.add_header('Cache-Control', 'no-cache')
        req.add_header('Pragma', 'no-cache')
        
        response = urllib2.urlopen(req, timeout=5)
        online_version = response.read().strip()
        
        # If online version is different, prompt the user
        if online_version and online_version != local_version:
            msg = "A new update (V{}) for the Riyan Revit Plugin Suite is available!\n".format(online_version)
            msg += "Please click the 'Update' button in the Riyan tab to install it."
            
            try:
                # Toast notification (slides from bottom right, very professional)
                forms.toast(msg, title="Riyan Tools Update", appid="Riyan Revit Plugin")
            except:
                # Fallback to TopMost MessageBox if toast fails
                import clr
                clr.AddReference("System.Windows.Forms")
                from System.Windows.Forms import MessageBox, MessageBoxButtons, MessageBoxIcon, MessageBoxOptions, MessageBoxDefaultButton
                MessageBox.Show(msg, "Riyan Tools Update", MessageBoxButtons.OK, MessageBoxIcon.Information, MessageBoxDefaultButton.Button1, MessageBoxOptions.ServiceNotification)
            
    except Exception as e:
        # Fails silently so it never interrupts the user's workflow
        pass

# Run the update check in a background thread so it doesn't block Revit startup
t = threading.Thread(target=check_for_updates)
t.start()
