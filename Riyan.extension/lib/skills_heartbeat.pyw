# -*- coding: utf-8 -*-
"""
skills_heartbeat.pyw - Silent Background Antigravity Skills Fleet Heartbeat
Runs silently with pythonw (no console window).
Polls cloud manifest every 5 minutes and keeps local Antigravity skills in real-time sync.
"""

import os
import sys
import time

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    import skills_sync
    # Starts daemon thread and keeps process alive silently
    skills_sync.start_heartbeat(interval_seconds=300)
    while True:
        time.sleep(3600)
except Exception:
    pass
