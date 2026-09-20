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
    riyan_shared_params.enforce_riyan_shared_parameters()
except Exception:
    pass
