#!/usr/bin/env python3
"""
VPN Automation Application Launcher

This script serves as the main entry point for the VPN Automation Application.
It sets up the Python path correctly and launches the application.
"""

import os
import sys

# Add the parent directory to the Python path to enable absolute imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Import and run the main function from integrated_main_window.py
from vpn_auto_app_final_may20_v3.src.ui.integrated_main_window import main

if __name__ == "__main__":
    main()
