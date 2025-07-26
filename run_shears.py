#!/usr/bin/env python3
"""
Shears launcher script
"""

import sys
from pathlib import Path

# Add the shears directory to Python path
shears_dir = Path(__file__).parent
sys.path.insert(0, str(shears_dir))

try:
    from shears.app import main
    main()
except ImportError as e:
    if "textual" in str(e):
        print("Error: textual library not found.")
        print("Please install it with: pip install textual rich")
        print("\nFor a basic test without TUI, run: python3 test_basic.py")
        sys.exit(1)
    else:
        raise