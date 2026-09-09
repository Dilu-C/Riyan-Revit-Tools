# -*- coding: utf-8 -*-
import os
import sys

curr = os.path.dirname(__file__)
ext_dir = None
for _ in range(6):
    if os.path.exists(os.path.join(curr, "whats_new.py")):
        ext_dir = curr
        break
    curr = os.path.dirname(curr)

if ext_dir and ext_dir not in sys.path:
    sys.path.insert(0, ext_dir)

try:
    import whats_new
    whats_new.show_whats_new()
except Exception as ex:
    from pyrevit import forms
    forms.alert("Could not open What's New window:\n" + str(ex), title="What's New")
