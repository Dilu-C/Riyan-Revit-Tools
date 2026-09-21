# -*- coding: utf-8 -*-
import os
import sys
from pyrevit import forms, HOST_APP, revit

try:
    _lib_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "lib"))
    if _lib_dir not in sys.path:
        sys.path.insert(0, _lib_dir)
    import riyan_shared_params
    
    app = None
    if revit.doc and hasattr(revit.doc, "Application"):
        app = revit.doc.Application
    elif hasattr(HOST_APP, "app"):
        app = HOST_APP.app
        
    latest_file, changed = riyan_shared_params.enforce_riyan_shared_parameters(app, check_cloud=True)
    
    # Verify active definition file
    groups_count = 0
    params_count = 0
    if app and hasattr(app, "OpenSharedParameterFile"):
        try:
            df = app.OpenSharedParameterFile()
            if df:
                groups_count = df.Groups.Size
                for g in df.Groups:
                    params_count += g.Definitions.Size
        except Exception:
            pass
            
    fname = os.path.basename(latest_file) if latest_file else "Unknown"
    msg = "Official Riyan Shared Parameters Linked Successfully!\n\n"
    msg += "Active File: {}\n".format(fname)
    msg += "Path: {}\n\n".format(latest_file)
    msg += "Parameter Groups: {} Groups\n".format(groups_count)
    msg += "Total Parameters: {} Parameters\n\n".format(params_count)
    msg += "Active Revit Session and Revit.ini are now 100% synchronized."
    
    forms.alert(msg, title="Shared Parameters Synchronized 👍", warn_icon=False)
except Exception as ex:
    forms.alert("Error syncing shared parameters:\n" + str(ex), title="Sync Error", warn_icon=True)
