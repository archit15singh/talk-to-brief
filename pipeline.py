#!/usr/bin/env python3
"""
Pipeline script for semantic chunking of transcript files using llama-index.
"""

import re
import os
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from llama_index.core import Document
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser import SemanticSplitterNodeParser
from openai_client import OpenAIClient, ChatMessage, CompletionConfig, ModelType

# Load environment variables from .env file
load_dotenv()

# ---------- CONFIG ----------
INPUT_TXT = "data/transcripts/building-scalable-apis.md"  # path to your transcript
BUFFER_SIZE = 3             # sentences in rolling window
BREAKPOINT_THRESHOLD = 92   # higher = fewer/larger chunks

# Data hierarchy structure
DATA_ROOT = Path("data")
PROCESSED_ROOT = DATA_ROOT / "processed"

def create_processing_directories(transcript_name):
    """Create directory structure for processing artifacts."""
    # Extract base name without extension
    base_name = Path(transcript_name).stem
    
    # Create processing directory structure
    process_dir = PROCESSED_ROOT / base_name
    
    dirs = {
        'base': process_dir,
        'cleaned': process_dir / "01_cleaned",
        'chunks': process_dir / "02_chunks", 
        'summaries': process_dir / "03_summaries",
        'metadata': process_dir / "metadata"
    }
    
    # Create all directories
    for dir_path in dirs.values():
        dir_path.mkdir(parents=True, exist_ok=True)
    
    return dirs

def save_processing_metadata(dirs, config, stats):
    """Save processing metadata and configuration."""
    metadata = {
        'timestamp': datetime.now().isoformat(),
        'config': config,
        'stats': stats,
        'pipeline_version': '1.0'
    }
    
    metadata_file = dirs['metadata'] / "processing_metadata.json"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    return metadata_file

def save_cleaned_text(dirs, raw_text, clean_text):
    """Save both raw and cleaned text with metadata."""
    # Save cleaned text
    cleaned_file = dirs['cleaned'] / "cleaned_transcript.txt"
    with open(cleaned_file, 'w', encoding='utf-8') as f:
        f.write(clean_text)
    
    # Save cleaning metadata
    cleaning_stats = {
        'raw_char_count': len(raw_text),
        'cleaned_char_count': len(clean_text),
        'reduction_ratio': 1 - (len(clean_text) / len(raw_text)) if raw_text else 0,
        'timestamp': datetime.now().isoformat()
    }
    
    metadata_file = dirs['cleaned'] / "cleaning_metadata.json"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(cleaning_stats, f, indent=2)
    
    return cleaned_file, cleaning_stats

def save_chunks(dirs, chunks, chunking_config):
    """Save individual chunks and chunk metadata."""
    chunk_files = []
    
    # Save each chunk as individual file
    for i, chunk in enumerate(chunks, 1):
        chunk_file = dirs['chunks'] / f"chunk_{i:03d}.txt"
        with open(chunk_file, 'w', encoding='utf-8') as f:
            f.write(chunk)
        chunk_files.append(chunk_file)
    
    # Save chunk index with metadata
    chunk_index = {
        'total_chunks': len(chunks),
        'chunking_config': chunking_config,
        'chunks': [
            {
                'chunk_id': i,
                'file': f"chunk_{i:03d}.txt",
                'char_count': len(chunk),
                'word_count': len(chunk.split()),
                'preview': chunk[:100] + "..." if len(chunk) > 100 else chunk
            }
            for i, chunk in enumerate(chunks, 1)
        ],
        'timestamp': datetime.now().isoformat()
    }
    
    index_file = dirs['chunks'] / "chunk_index.json"
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(chunk_index, f, indent=2, ensure_ascii=False)
    
    return chunk_files, index_file

def save_summaries(dirs, summaries):
    """Save individual summaries and summary metadata."""
    summary_files = []
    
    # Save each summary as individual file with traceability
    for summary_data in summaries:
        chunk_num = summary_data['chunk_number']
        summary_file = dirs['summaries'] / f"summary_{chunk_num:03d}.txt"
        
        # Create summary with traceability header
        summary_content = f"""# Summary for Chunk {chunk_num}
Source: chunk_{chunk_num:03d}.txt
Generated: {datetime.now().isoformat()}
Original Length: {summary_data['char_count']} characters

## Summary
{summary_data['summary']}
"""
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary_content)
        summary_files.append(summary_file)
    
    # Save summary index
    summary_index = {
        'total_summaries': len(summaries),
        'summaries': [
            {
                'chunk_id': s['chunk_number'],
                'summary_file': f"summary_{s['chunk_number']:03d}.txt",
                'source_chunk': f"chunk_{s['chunk_number']:03d}.txt",
                'original_chars': s['char_count'],
                'summary_chars': len(s['summary']),
                'compression_ratio': len(s['summary']) / s['char_count'] if s['char_count'] > 0 else 0
            }
            for s in summaries
        ],
        'timestamp': datetime.now().isoformat()
    }
    
    index_file = dirs['summaries'] / "summary_index.json"
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(summary_index, f, indent=2, ensure_ascii=False)
    
    return summary_files, index_file

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

def load_and_chunk_transcript(file_path, dirs):
    """Load transcript and perform semantic chunking with artifact saving."""
    try:
        # Load raw text
        with open(file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
        
        # Clean the text
        clean_text = clean_transcript_text(raw_text)
        
        # Save cleaned text artifacts
        cleaned_file, cleaning_stats = save_cleaned_text(dirs, raw_text, clean_text)
        print(f"✓ Saved cleaned text: {cleaned_file}")
        print(f"  Reduction: {cleaning_stats['reduction_ratio']:.1%}")
        
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
        
        # Save chunk artifacts
        chunking_config = {
            'buffer_size': BUFFER_SIZE,
            'breakpoint_threshold': BREAKPOINT_THRESHOLD,
            'embedding_model': 'text-embedding-ada-002'
        }
        
        chunk_files, chunk_index = save_chunks(dirs, chunks, chunking_config)
        print(f"✓ Saved {len(chunks)} chunks: {dirs['chunks']}")
        print(f"  Chunk index: {chunk_index}")
        
        return chunks, clean_text, cleaning_stats
        
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return None, None, None
    except Exception as e:
        print(f"Error processing file: {e}")
        return None, None, None

def summarize_chunks(chunks, dirs):
    """Summarize each chunk using OpenAI with artifact saving."""
    client = OpenAIClient()
    config = CompletionConfig(model=ModelType.GPT_4O_MINI, temperature=0.3)
    
    summaries = []
    
    print("\n" + "=" * 40)
    print("GENERATING SUMMARIES:")
    print("=" * 40)
    
    for i, chunk in enumerate(chunks, 1):
        print(f"Summarizing chunk {i}/{len(chunks)}...")
        
        try:
            summary = client.simple_prompt(
                prompt=f"Summarize the following text in 2-3 sentences:\n\n{chunk}",
                system_message="You are a helpful assistant that creates concise, accurate summaries.",
                config=config
            )
            summaries.append({
                'chunk_number': i,
                'original_text': chunk,
                'summary': summary.strip(),
                'char_count': len(chunk)
            })
            
            print(f"✓ Chunk {i} summarized ({len(chunk)} chars → {len(summary.strip())} chars)")
            
        except Exception as e:
            print(f"✗ Error summarizing chunk {i}: {e}")
            summaries.append({
                'chunk_number': i,
                'original_text': chunk,
                'summary': f"Error: Could not summarize - {str(e)}",
                'char_count': len(chunk)
            })
    
    # Save summary artifacts
    summary_files, summary_index = save_summaries(dirs, summaries)
    print(f"✓ Saved {len(summaries)} summaries: {dirs['summaries']}")
    print(f"  Summary index: {summary_index}")
    
    return summaries

def main():
    """Main pipeline function with full artifact tracking."""
    print("=" * 60)
    print("SEMANTIC TRANSCRIPT CHUNKING & SUMMARIZATION PIPELINE")
    print("=" * 60)
    print(f"Processing transcript: {INPUT_TXT}")
    print(f"Buffer size: {BUFFER_SIZE} sentences")
    print(f"Breakpoint threshold: {BREAKPOINT_THRESHOLD}%")
    print("=" * 60)
    print()
    
    # Create processing directories
    transcript_name = Path(INPUT_TXT).name
    dirs = create_processing_directories(transcript_name)
    print(f"✓ Created processing directories: {dirs['base']}")
    
    # Process transcript with artifact saving
    chunks, clean_text, cleaning_stats = load_and_chunk_transcript(INPUT_TXT, dirs)
    
    if chunks:
        print(f"Successfully processed transcript into {len(chunks)} semantic chunks")
        
        # Generate summaries for each chunk
        summaries = summarize_chunks(chunks, dirs)
        
        # Save overall processing metadata
        config = {
            'input_file': INPUT_TXT,
            'buffer_size': BUFFER_SIZE,
            'breakpoint_threshold': BREAKPOINT_THRESHOLD,
            'model': 'gpt-4o-mini'
        }
        
        stats = {
            'total_chunks': len(chunks),
            'total_summaries': len(summaries),
            'cleaning_stats': cleaning_stats,
            'avg_chunk_size': sum(len(c) for c in chunks) / len(chunks) if chunks else 0
        }
        
        metadata_file = save_processing_metadata(dirs, config, stats)
        print(f"✓ Saved processing metadata: {metadata_file}")
        
        print("\n" + "=" * 60)
        print("PIPELINE COMPLETE - ARTIFACTS SAVED")
        print("=" * 60)
        print(f"Processing directory: {dirs['base']}")
        print(f"├── 01_cleaned/     - Cleaned transcript")
        print(f"├── 02_chunks/      - {len(chunks)} semantic chunks")
        print(f"├── 03_summaries/   - {len(summaries)} summaries")
        print(f"└── metadata/       - Processing metadata")
        
        print("\n" + "=" * 40)
        print("SAMPLE RESULTS:")
        print("=" * 40)
        
        for summary_data in summaries[:2]:  # Show first 2 summaries
            print(f"\n--- Chunk {summary_data['chunk_number']} Summary ---")
            print(f"Original: {summary_data['char_count']} chars")
            print(f"Summary: {summary_data['summary']}")
        
        if len(summaries) > 2:
            print(f"\n... and {len(summaries) - 2} more summaries")
        
        print(f"\nTraceability: Each summary links back to its source chunk")
        print(f"All artifacts preserved in: {dirs['base']}")
        
        # Return processing results and directory info
        return {
            'chunks': chunks,
            'summaries': summaries,
            'dirs': dirs,
            'stats': stats
        }
    else:
        print("Failed to process transcript.")
        return None

if __name__ == "__main__":
    main()