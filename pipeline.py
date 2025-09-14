#!/usr/bin/env python3
"""
Pipeline launcher - runs the main pipeline from src/
"""

import sys
import os
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import and run the main pipeline
from pipeline import main

if __name__ == "__main__":
    main()