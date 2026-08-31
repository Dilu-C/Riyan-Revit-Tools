import os
import threading
import time
from pyrevit.coreutils import git

def check_updates_loop():
    # Wait 10 seconds after Revit startup before the first check
    time.sleep(10)
    
    last_notified_sha = None
    
    while True:
        try:
            # Determine the git repository root path
            current_dir = os.path.dirname(__file__)
            repo_dir = os.path.dirname(current_dir)
            
            # Check if the folder is indeed a git repository
            if not os.path.exists(os.path.join(repo_dir, ".git")):
                time.sleep(7200)
                continue
                
            repo = git.get_repo(repo_dir)
            
            # Run a fetch to check for remote updates
            git.git_fetch(repo)
            
            # Compare local and remote heads
            div = git.compare_branch_heads(repo)
            
            # If local is behind remote, trigger the update prompt
            if div and div.BehindBy > 0:
                # Safely get the remote tip commit SHA
                remote_sha = None
                try:
                    remote_sha = repo.repo.Head.TrackedBranch.Tip.Id.Sha
                except Exception:
                    pass
                
                # Prompt only if we haven't prompted for this specific commit hash yet
                if not remote_sha or remote_sha != last_notified_sha:
                    from System.Windows import MessageBox, MessageBoxButton, MessageBoxImage, MessageBoxResult
                    
                    res = MessageBox.Show(
                        u"An update is available for Riyan Revit Tools.\nWould you like to install the update now?",
                        u"Riyan Tools Update Available",
                        MessageBoxButton.YesNo,
                        MessageBoxImage.Information
                    )
                    
                    if res == MessageBoxResult.Yes:
                        git.git_pull(repo)
                        
                        MessageBox.Show(
                            u"Update installed successfully!\n\nPlease click pyRevit 'Reload' (in the pyRevit tab) to apply the changes.",
                            u"Update Success",
                            MessageBoxButton.OK,
                            MessageBoxImage.Information
                        )
                    else:
                        # If they skip, remember this SHA so we don't prompt them again for the same update
                        if remote_sha:
                            last_notified_sha = remote_sha
        except Exception:
            # Fail silently so it never interrupts Revit operations
            pass
            
        # Check every 2 hours (7200 seconds)
        time.sleep(7200)

# Run the update check loop on a background thread
t = threading.Thread(target=check_updates_loop)
t.daemon = True
t.start()
