#!/usr/bin/env python3
"""Launcher script for STT Keyboard (used by PyInstaller)."""

import sys
import os
import multiprocessing

# CRITICAL: Must be called before any other multiprocessing code for frozen apps
if __name__ == "__main__":
    multiprocessing.freeze_support()
    multiprocessing.set_start_method('spawn', force=True)

# Add mickey package to path
if getattr(sys, 'frozen', False):
    # Running as frozen app
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, base_path)

# Now import and run the app
from mickey.app import main

if __name__ == "__main__":
    main()
