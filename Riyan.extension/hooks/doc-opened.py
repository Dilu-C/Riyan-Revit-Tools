# -*- coding: utf-8 -*-
"""
pyRevit Hook: doc-opened
Ensures Riyan Standard Shared Parameters are strictly active on project open.
"""

import os
import sys

try:
    _lib_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "lib"))
    if _lib_dir not in sys.path:
        sys.path.insert(0, _lib_dir)
    import riyan_shared_params
    app = None
    try:
        from pyrevit import EXEC_PARAMS
        if hasattr(EXEC_PARAMS, "event_args") and hasattr(EXEC_PARAMS.event_args, "Document"):
            doc = EXEC_PARAMS.event_args.Document
            if doc and hasattr(doc, "Application"):
                app = doc.Application
    except Exception:
        pass
    riyan_shared_params.enforce_riyan_shared_parameters(app)
except Exception:
    pass
