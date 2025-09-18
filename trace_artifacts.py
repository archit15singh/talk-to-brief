#!/usr/bin/env python3
"""
Script to demonstrate traceability through pipeline artifacts.
Shows how to trace from original transcript → chunks → summaries.
"""

import json
from pathlib import Path

def trace_processing_artifacts(transcript_name):
    """Trace artifacts for a given transcript through the pipeline."""
    base_name = Path(transcript_name).stem
    process_dir = Path("data/processed") / base_name
    
    if not process_dir.exists():
        print(f"No processing artifacts found for: {transcript_name}")
        return
    
    print("=" * 60)
    print(f"TRACING ARTIFACTS FOR: {transcript_name}")
    print("=" * 60)
    
    # Load processing metadata
    metadata_file = process_dir / "metadata" / "processing_metadata.json"
    if metadata_file.exists():
        with open(metadata_file) as f:
            metadata = json.load(f)
        
        print(f"Processed: {metadata['timestamp']}")
        print(f"Pipeline version: {metadata['pipeline_version']}")
        print(f"Total chunks: {metadata['stats']['total_chunks']}")
        print(f"Total summaries: {metadata['stats']['total_summaries']}")
        print()
    
    # Show cleaning stage
    cleaning_metadata = process_dir / "01_cleaned" / "cleaning_metadata.json"
    if cleaning_metadata.exists():
        with open(cleaning_metadata) as f:
            cleaning = json.load(f)
        
        print("STAGE 1: CLEANING")
        print(f"├── Raw text: {cleaning['raw_char_count']:,} characters")
        print(f"├── Cleaned text: {cleaning['cleaned_char_count']:,} characters")
        print(f"└── Reduction: {cleaning['reduction_ratio']:.1%}")
        print()
    
    # Show chunking stage
    chunk_index = process_dir / "02_chunks" / "chunk_index.json"
    if chunk_index.exists():
        with open(chunk_index) as f:
            chunks = json.load(f)
        
        print("STAGE 2: CHUNKING")
        print(f"├── Total chunks: {chunks['total_chunks']}")
        print(f"├── Buffer size: {chunks['chunking_config']['buffer_size']}")
        print(f"└── Breakpoint threshold: {chunks['chunking_config']['breakpoint_threshold']}")
        
        # Show first few chunks
        for chunk in chunks['chunks'][:3]:
            print(f"    ├── {chunk['file']}: {chunk['char_count']} chars")
            print(f"    │   Preview: {chunk['preview']}")
        
        if len(chunks['chunks']) > 3:
            print(f"    └── ... and {len(chunks['chunks']) - 3} more chunks")
        print()
    
    # Show summarization stage
    summary_index = process_dir / "03_summaries" / "summary_index.json"
    if summary_index.exists():
        with open(summary_index) as f:
            summaries = json.load(f)
        
        print("STAGE 3: SUMMARIZATION")
        print(f"├── Total summaries: {summaries['total_summaries']}")
        
        # Show traceability for first few summaries
        for summary in summaries['summaries'][:3]:
            print(f"├── {summary['summary_file']}")
            print(f"│   ├── Source: {summary['source_chunk']}")
            print(f"│   ├── Compression: {summary['compression_ratio']:.1%}")
            print(f"│   └── {summary['original_chars']} → {summary['summary_chars']} chars")
        
        if len(summaries['summaries']) > 3:
            print(f"└── ... and {len(summaries['summaries']) - 3} more summaries")
        print()
    
    print("TRACEABILITY CHAIN:")
    print("Original transcript → 01_cleaned/cleaned_transcript.txt")
    print("                  → 02_chunks/chunk_XXX.txt")
    print("                  → 03_summaries/summary_XXX.txt")
    print()
    print(f"All artifacts preserved in: {process_dir}")

def show_specific_trace(transcript_name, chunk_number):
    """Show detailed trace for a specific chunk."""
    base_name = Path(transcript_name).stem
    process_dir = Path("data/processed") / base_name
    
    print("=" * 60)
    print(f"DETAILED TRACE: {transcript_name} → Chunk {chunk_number}")
    print("=" * 60)
    
    # Read original chunk
    chunk_file = process_dir / "02_chunks" / f"chunk_{chunk_number:03d}.txt"
    if chunk_file.exists():
        with open(chunk_file) as f:
            chunk_text = f.read()
        
        print("ORIGINAL CHUNK:")
        print("-" * 40)
        print(chunk_text[:300] + "..." if len(chunk_text) > 300 else chunk_text)
        print()
    
    # Read corresponding summary
    summary_file = process_dir / "03_summaries" / f"summary_{chunk_number:03d}.txt"
    if summary_file.exists():
        with open(summary_file) as f:
            summary_content = f.read()
        
        print("GENERATED SUMMARY:")
        print("-" * 40)
        print(summary_content)

if __name__ == "__main__":
    # Example usage
    transcript_name = "building-scalable-apis.md"
    
    # Show full trace
    trace_processing_artifacts(transcript_name)
    
    # Show detailed trace for chunk 1
    print("\n" + "=" * 60)
    show_specific_trace(transcript_name, 1)