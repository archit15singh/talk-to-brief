#!/usr/bin/env python3
"""
Pipeline script for semantic chunking of transcript files using llama-index.
"""

import re
import os
from pathlib import Path
from dotenv import load_dotenv
from llama_index.core import Document
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser import SemanticSplitterNodeParser

# Load environment variables from .env file
load_dotenv()

# ---------- CONFIG ----------
INPUT_TXT = "data/transcripts/building-scalable-apis.md"  # path to your transcript
BUFFER_SIZE = 3             # sentences in rolling window
BREAKPOINT_THRESHOLD = 92   # higher = fewer/larger chunks

def clean_transcript_text(raw_text):
    """Clean transcript text by removing timestamps, speaker labels, and filler words."""
    # Remove timestamps like [12:34] or 12:34:56
    clean_text = re.sub(r"\[?\d{1,2}:\d{2}(?::\d{2})?\]?", " ", raw_text)
    
    # Remove stage directions like (applause), (laughter), (music)
    clean_text = re.sub(r"\(\s*(applause|laughter|music)\s*\)", " ", clean_text, flags=re.I)
    
    # Remove speaker labels like "Speaker Name:" at start of lines
    clean_text = re.sub(r"(?m)^\s*[A-Z][A-Za-z0-9_\- ]{1,30}:\s+", "", clean_text)
    
    # Normalize whitespace
    clean_text = re.sub(r"\s+", " ", clean_text).strip()
    
    return clean_text

def load_and_chunk_transcript(file_path):
    """Load transcript and perform semantic chunking."""
    try:
        # Load raw text
        with open(file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
        
        # Clean the text
        clean_text = clean_transcript_text(raw_text)
        
        # Create document
        doc = Document(text=clean_text)
        
        # Set up semantic chunking
        embed = OpenAIEmbedding()
        parser = SemanticSplitterNodeParser(
            embed_model=embed,
            buffer_size=BUFFER_SIZE,
            breakpoint_percentile_threshold=BREAKPOINT_THRESHOLD
        )
        
        # Generate semantic chunks
        nodes = parser.get_nodes_from_documents([doc])
        
        # Extract chunked strings
        chunks = [n.get_content() for n in nodes]
        
        return chunks, clean_text
        
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return None, None
    except Exception as e:
        print(f"Error processing file: {e}")
        return None, None

def main():
    """Main pipeline function."""
    print("=" * 60)
    print("SEMANTIC TRANSCRIPT CHUNKING PIPELINE")
    print("=" * 60)
    print(f"Processing transcript: {INPUT_TXT}")
    print(f"Buffer size: {BUFFER_SIZE} sentences")
    print(f"Breakpoint threshold: {BREAKPOINT_THRESHOLD}%")
    print("=" * 60)
    print()
    
    chunks, clean_text = load_and_chunk_transcript(INPUT_TXT)
    
    if chunks:
        print(f"Successfully processed transcript into {len(chunks)} semantic chunks")
        print("\n" + "=" * 40)
        print("CHUNKS PREVIEW:")
        print("=" * 40)
        
        for i, chunk in enumerate(chunks[:3], 1):  # Show first 3 chunks
            print(f"\n--- Chunk {i} ({len(chunk)} chars) ---")
            print(chunk[:200] + "..." if len(chunk) > 200 else chunk)
        
        if len(chunks) > 3:
            print(f"\n... and {len(chunks) - 3} more chunks")
        
        # Optionally return the full chunks list for programmatic use
        return chunks
    else:
        print("Failed to process transcript.")
        return None

if __name__ == "__main__":
    main()