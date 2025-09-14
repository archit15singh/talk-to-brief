#!/usr/bin/env python3
"""
Setup launcher - runs the recording setup from src/
"""

import sys
import os
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import and run the setup
from setup_recording import main

if __name__ == "__main__":
    main()