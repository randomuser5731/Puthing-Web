#!/usr/bin/env python3
"""
Puthing Around - Server Launcher (no console)
==============================================
Run this file to start the server without a console window.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from puthing_gui import PuthingGUI

if __name__ == "__main__":
    app = PuthingGUI()
    app.run()
