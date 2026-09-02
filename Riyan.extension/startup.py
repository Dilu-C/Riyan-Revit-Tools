import os
import urllib2
import json
import threading
import time
import traceback
from pyrevit import revit, forms, script

def check_for_updates():
    try:
        # Give Revit time to fully load UI
        time.sleep(15)
        
        # Determine paths
        extension_dir = os.path.dirname(os.path.dirname(__file__))
        git_dir = os.path.join(extension_dir, '.git')
        
        # Only use pyrevit.coreutils.git if it's an actual Git repo
        if os.path.exists(git_dir):
            try:
                from pyrevit.coreutils import git
                repo = git.get_repo(extension_dir)
                if repo:
                    if git.check_for_updates(repo):
                        forms.alert("A new update is available for Riyan Revit Tools!\n\nPlease double-click the 'Install_Riyan_Tools.bat' file on your Desktop to update.", title="Riyan Tools Update")
            except Exception as e:
                pass
        else:
            # Not a git repo (probably installed via ZIP 1-Click installer)
            # You could implement a pure Python GitHub API check here if needed,
            # but for now, we just gracefully do nothing so it doesn't crash.
            pass
            
    except Exception as e:
        pass

# Run the update check in a background thread so it doesn't block Revit startup
t = threading.Thread(target=check_for_updates)
t.start()
