# -*- coding: utf-8 -*-
import os
import sys

ext_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if ext_dir not in sys.path:
    sys.path.insert(0, ext_dir)

try:
    import whats_new
    whats_new.show_whats_new()
except Exception as ex:
    from pyrevit import forms
    forms.alert("Could not open What's New window: " + str(ex))
