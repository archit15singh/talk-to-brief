#!/usr/bin/env python3
"""
Recording launcher - runs the recording + processing workflow from src/
"""

import sys
import os
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import and run the recording workflow
from record_and_process import main

if __name__ == "__main__":
    main()