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
        local_version_file = os.path.join(extension_dir, 'version.txt')
        
        # Default local version
        local_version = "1.0"
        if os.path.exists(local_version_file):
            with open(local_version_file, 'r') as f:
                local_version = f.read().strip()
                
        # Fetch online version directly from GitHub raw content
        url = "https://raw.githubusercontent.com/Dilu-C/Riyan-Revit-Tools/main/version.txt"
        req = urllib2.Request(url)
        # Prevent caching
        req.add_header('Cache-Control', 'no-cache')
        req.add_header('Pragma', 'no-cache')
        
        response = urllib2.urlopen(req, timeout=5)
        online_version = response.read().strip()
        
        # If online version is different, prompt the user
        if online_version and online_version != local_version:
            msg = "A new update (v{}) is available for Riyan Revit Tools!\n\n".format(online_version)
            msg += "Please click the 'Update' button in the Riyan tab to install it."
            forms.alert(msg, title="Riyan Tools Update")
            
    except Exception as e:
        # Fails silently so it never interrupts the user's workflow
        pass

# Run the update check in a background thread so it doesn't block Revit startup
t = threading.Thread(target=check_for_updates)
t.start()
