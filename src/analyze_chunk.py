#!/usr/bin/env python3
"""
Intelligent chunking and parallel GPT-4 analysis of transcripts.
Processes transcript.txt into ~1200 word chunks and analyzes each with GPT-4.
"""

import os
import sys
import json
import re
import asyncio
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any
import openai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def load_transcript(transcript_path: str = "data/transcripts/transcript.txt") -> str:
    """Load transcript content from file."""
    if not os.path.exists(transcript_path):
        raise FileNotFoundError(f"Transcript file not found: {transcript_path}")
    
    with open(transcript_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return content

def extract_transcript_text(content: str) -> str:
    """Extract just the spoken text from the transcript, preserving timestamps."""
    lines = content.split('\n')
    transcript_text = []
    
    for line in lines:
        line = line.strip()
        # Skip header lines and word-level timestamps
        if (line.startswith('#') or 
            line.startswith('Audio:') or 
            line.startswith('Language:') or 
            line.startswith('Duration:') or
            line == '' or
            re.match(r'^\s*\d{2}:\d{2}-\d{2}:\d{2}:', line)):
            continue
        
        # Extract timestamped segments
        if re.match(r'^\[.*?\]', line):
            transcript_text.append(line)
    
    return '\n'.join(transcript_text)

def intelligent_chunk(text: str, target_words: int = 1200) -> List[str]:
    """
    Split transcript into chunks of approximately target_words, 
    respecting sentence boundaries and timestamp segments.
    """
    lines = text.split('\n')
    chunks = []
    current_chunk = []
    current_word_count = 0
    
    for line in lines:
        if not line.strip():
            continue
            
        # Count words in this line (excluding timestamp brackets)
        text_part = re.sub(r'^\[.*?\]\s*', '', line)
        words_in_line = len(text_part.split())
        
        # If adding this line would exceed target, start new chunk
        if current_word_count + words_in_line > target_words and current_chunk:
            chunks.append('\n'.join(current_chunk))
            current_chunk = [line]
            current_word_count = words_in_line
        else:
            current_chunk.append(line)
            current_word_count += words_in_line
    
    # Add the last chunk if it has content
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
    
    return chunks

def load_prompt_template() -> str:
    """Load the per-chunk analysis prompt template."""
    prompt_path = "config/per_chunk.md"
    if not os.path.exists(prompt_path):
        raise FileNotFoundError(f"Prompt template not found: {prompt_path}")
    
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()

def analyze_chunk_with_gpt4(chunk: str, chunk_index: int, prompt_template: str) -> Dict[str, Any]:
    """Analyze a single chunk using GPT-4."""
    try:
        # Validate API key
        if not os.getenv('OPENAI_API_KEY'):
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        client = openai.OpenAI()
        
        # Prepare the full prompt
        full_prompt = f"{prompt_template}\n\n## Transcript Chunk {chunk_index + 1}:\n\n{chunk}"
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert at analyzing conference talks and creating actionable insights."},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.3,
            max_tokens=1500,
            timeout=60  # 60 second timeout per API call
        )
        
        analysis = response.choices[0].message.content
        
        return {
            "chunk_index": chunk_index,
            "chunk_text": chunk,
            "analysis": analysis,
            "word_count": len(chunk.split()),
            "success": True
        }
        
    except Exception as e:
        return {
            "chunk_index": chunk_index,
            "chunk_text": chunk,
            "error": str(e),
            "success": False
        }

def process_chunks_parallel(chunks: List[str], prompt_template: str, max_workers: int = 4) -> List[Dict[str, Any]]:
    """Process all chunks in parallel using ThreadPoolExecutor."""
    print(f"Processing {len(chunks)} chunks in parallel (max {max_workers} workers)...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(analyze_chunk_with_gpt4, chunk, i, prompt_template)
            for i, chunk in enumerate(chunks)
        ]
        
        results = []
        for i, future in enumerate(futures):
            try:
                result = future.result(timeout=120)  # 2 minute timeout per chunk
                if result["success"]:
                    print(f"✓ Chunk {i + 1}/{len(chunks)} completed ({result['word_count']} words)")
                else:
                    print(f"✗ Chunk {i + 1}/{len(chunks)} failed: {result['error']}")
                results.append(result)
            except Exception as e:
                print(f"✗ Chunk {i + 1}/{len(chunks)} timeout/error: {e}")
                results.append({
                    "chunk_index": i,
                    "error": str(e),
                    "success": False
                })
    
    return results

def save_partials(results: List[Dict[str, Any]], output_dir: str = "data/partials") -> None:
    """Save analysis results to individual JSON files in partials/ directory."""
    # Create output directory
    Path(output_dir).mkdir(exist_ok=True)
    
    successful_saves = 0
    for result in results:
        chunk_index = result["chunk_index"]
        output_file = f"{output_dir}/chunk_{chunk_index:02d}.json"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            if result["success"]:
                successful_saves += 1
                print(f"Saved: {output_file}")
            else:
                print(f"Saved (with errors): {output_file}")
                
        except Exception as e:
            print(f"Failed to save {output_file}: {e}")
    
    print(f"\nSummary: {successful_saves}/{len(results)} chunks analyzed successfully")
    print(f"Partial results saved to: {output_dir}/")

def analyze_transcript(transcript_path: str, output_dir: str) -> bool:
    """Analyze transcript and save partials. Returns True if successful."""
    try:
        # Validate environment
        if not os.getenv('OPENAI_API_KEY'):
            print("Error: OPENAI_API_KEY environment variable not set")
            print("Please set your OpenAI API key: export OPENAI_API_KEY='your-key-here'")
            return False
        
        # Load transcript
        print("Loading transcript...")
        transcript_content = load_transcript(transcript_path)
        transcript_text = extract_transcript_text(transcript_content)
        
        if not transcript_text.strip():
            print("Error: No transcript content found")
            return False
        
        # Create intelligent chunks
        print("Creating intelligent chunks...")
        chunks = intelligent_chunk(transcript_text, target_words=1200)
        print(f"Created {len(chunks)} chunks")
        
        for i, chunk in enumerate(chunks):
            word_count = len(chunk.split())
            print(f"  Chunk {i + 1}: {word_count} words")
        
        # Load prompt template
        print("Loading analysis prompt...")
        prompt_template = load_prompt_template()
        
        # Process chunks in parallel
        results = process_chunks_parallel(chunks, prompt_template, max_workers=4)
        
        # Save results
        save_partials(results, output_dir)
        
        # Final summary
        successful = sum(1 for r in results if r["success"])
        print(f"\nAnalysis complete: {successful}/{len(results)} chunks processed successfully")
        
        return successful > 0
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Main entry point for chunk analysis."""
    transcript_path = sys.argv[1] if len(sys.argv) > 1 else "data/transcripts/transcript.txt"
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "data/partials"
    
    success = analyze_transcript(transcript_path, output_dir)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()