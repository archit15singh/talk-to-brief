#!/usr/bin/env python3
"""
Pipeline script to read and print transcript files.
"""

import os
from pathlib import Path

def read_transcript(file_path):
    """Read transcript file and return its content."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return None
    except Exception as e:
        print(f"Error reading file: {e}")
        return None

def main():
    """Main pipeline function."""
    transcript_path = "data/transcripts/building-scalable-apis.md"
    
    print("=" * 60)
    print("TRANSCRIPT READER PIPELINE")
    print("=" * 60)
    print(f"Reading transcript: {transcript_path}")
    print("=" * 60)
    print()
    
    content = read_transcript(transcript_path)
    
    if content:
        print(content)
    else:
        print("Failed to read transcript.")

if __name__ == "__main__":
    main()