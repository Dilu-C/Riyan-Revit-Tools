import os
import threading
import time
from pyrevit.coreutils import git

def check_updates():
    # Allow Revit a few seconds to fully start up and stabilize
    time.sleep(5)
    
    try:
        # Determine the git repository root path
        current_dir = os.path.dirname(__file__)
        repo_dir = os.path.dirname(current_dir)
        
        # Check if the folder is indeed a git repository
        if not os.path.exists(os.path.join(repo_dir, ".git")):
            return
            
        repo = git.get_repo(repo_dir)
        
        # Run a fetch to check for remote updates
        git.git_fetch(repo)
        
        # Compare local and remote heads
        div = git.compare_branch_heads(repo)
        
        # If local is behind remote, trigger the update prompt
        if div and div.BehindBy > 0:
            from System.Windows import MessageBox, MessageBoxButton, MessageBoxImage, MessageBoxResult
            
            res = MessageBox.Show(
                u"An update is available for Riyan Revit Tools.\nWould you like to install the update now?",
                u"Riyan Tools Update",
                MessageBoxButton.YesNo,
                MessageBoxImage.Information
            )
            
            if res == MessageBoxResult.Yes:
                # Perform the git pull
                git.git_pull(repo)
                
                MessageBox.Show(
                    u"Update installed successfully!\n\nPlease click pyRevit 'Reload' (in the pyRevit tab) to apply the changes.",
                    u"Update Success",
                    MessageBoxButton.OK,
                    MessageBoxImage.Information
                )
    except Exception:
        # Fail silently so it never interrupts Revit startup
        pass

# Run the update check on a background thread to prevent blocking Revit startup
t = threading.Thread(target=check_updates)
t.daemon = True
t.start()
