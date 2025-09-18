#!/usr/bin/env python3
"""
Configuration and infrastructure settings
"""

from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ---------- CONFIG ----------
INPUT_TXT = "data/transcripts/building-scalable-apis.txt"  # path to your transcript
BUFFER_SIZE = 3             # sentences in rolling window
BREAKPOINT_THRESHOLD = 92   # higher = fewer/larger chunks

# Advanced chunking config
MIN_CHUNK_SIZE = 500        # minimum characters per chunk
MAX_CHUNK_SIZE = 3000       # maximum characters per chunk
OVERLAP_SIZE = 100          # character overlap between chunks

# Data hierarchy structure
DATA_ROOT = Path("data")
PROCESSED_ROOT = DATA_ROOT / "processed"