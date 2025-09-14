#!/usr/bin/env python3
"""
Intelligent chunking and parallel GPT-4 analysis script.
Processes transcripts into ~1200 word chunks and analyzes them with GPT-4.
"""

import sys
import os
import json
import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def validate_openai_api_key():
    """
    Validate OPENAI_API_KEY is present and properly formatted.
    
    Returns:
        str: The validated API key
        
    Raises:
        ValueError: If API key is missing or invalid
    """
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY environment variable not set. "
            "Please add your OpenAI API key to the .env file."
        )
    
    # Basic format validation for OpenAI API keys
    if not api_key.startswith('sk-'):
        raise ValueError(
            "Invalid OPENAI_API_KEY format. OpenAI API keys should start with 'sk-'"
        )
    
    if len(api_key) < 20:
        raise ValueError(
            "OPENAI_API_KEY appears to be too short. Please check your API key."
        )
    
    return api_key

def load_transcript(transcript_path: str) -> str:
    """Load transcript content from file."""
    if not os.path.exists(transcript_path):
        raise FileNotFoundError(f"Transcript file not found: {transcript_path}")
    
    with open(transcript_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return content

def extract_segments_from_transcript(transcript_content: str) -> List[str]:
    """Extract timestamped segments from transcript, skipping metadata."""
    lines = transcript_content.split('\n')
    segments = []
    
    for line in lines:
        line = line.strip()
        # Match lines with timestamp format [mm:ss -> mm:ss] content
        if re.match(r'^\[\d{2}:\d{2} -> \d{2}:\d{2}\]', line):
            segments.append(line)
    
    return segments

def create_intelligent_chunks(segments: List[str], target_words: int = 1200) -> List[Dict[str, Any]]:
    """
    Create intelligent chunks of ~1200 words each, respecting sentence boundaries.
    """
    chunks = []
    current_chunk = []
    current_word_count = 0
    chunk_index = 0
    
    for segment in segments:
        # Count words in this segment
        segment_words = len(segment.split())
        
        # If adding this segment would exceed target and we have content, start new chunk
        if current_word_count + segment_words > target_words and current_chunk:
            # Save current chunk
            chunk_text = '\n'.join(current_chunk)
            chunks.append({
                'chunk_index': chunk_index,
                'chunk_text': chunk_text,
                'word_count': current_word_count
            })
            
            # Start new chunk
            current_chunk = [segment]
            current_word_count = segment_words
            chunk_index += 1
        else:
            # Add to current chunk
            current_chunk.append(segment)
            current_word_count += segment_words
    
    # Don't forget the last chunk
    if current_chunk:
        chunk_text = '\n'.join(current_chunk)
        chunks.append({
            'chunk_index': chunk_index,
            'chunk_text': chunk_text,
            'word_count': current_word_count
        })
    
    return chunks

def load_analysis_prompt() -> str:
    """Load the per-chunk analysis prompt from config."""
    prompt_path = "config/per_chunk.md"
    if not os.path.exists(prompt_path):
        raise FileNotFoundError(f"Analysis prompt not found: {prompt_path}")
    
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()

def analyze_chunk_with_gpt4(chunk: Dict[str, Any], prompt: str) -> Dict[str, Any]:
    """
    Analyze a single chunk using GPT-4.
    """
    try:
        # Validate API key
        api_key = validate_openai_api_key()
        client = openai.OpenAI(api_key=api_key)
        
        # Prepare the full prompt
        full_prompt = f"{prompt}\n\n# Transcript Chunk:\n{chunk['chunk_text']}"
        
        # Call GPT-4 with retry logic and better error handling
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing conference talk transcripts and creating structured summaries."},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=0.3,
                max_tokens=2000,
                timeout=60  # 60 second timeout
            )
        except openai.RateLimitError as e:
            raise Exception(f"OpenAI rate limit exceeded: {e}")
        except openai.APIError as e:
            raise Exception(f"OpenAI API error: {e}")
        except openai.AuthenticationError as e:
            raise Exception(f"OpenAI authentication failed - check your API key: {e}")
        except Exception as e:
            raise Exception(f"OpenAI request failed: {e}")
        
        analysis = response.choices[0].message.content
        
        return {
            'chunk_index': chunk['chunk_index'],
            'chunk_text': chunk['chunk_text'],
            'analysis': analysis,
            'word_count': chunk['word_count'],
            'success': True
        }
        
    except Exception as e:
        print(f"Error analyzing chunk {chunk['chunk_index']}: {e}")
        return {
            'chunk_index': chunk['chunk_index'],
            'chunk_text': chunk['chunk_text'],
            'analysis': f"Error: {str(e)}",
            'word_count': chunk['word_count'],
            'success': False
        }

def process_chunks_parallel(chunks: List[Dict[str, Any]], prompt: str, max_workers: int = 4) -> List[Dict[str, Any]]:
    """
    Process chunks in parallel using ThreadPoolExecutor.
    Limited to 4 workers to respect OpenAI rate limits.
    """
    results = []
    
    print(f"Processing {len(chunks)} chunks in parallel (max {max_workers} workers)...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_chunk = {
            executor.submit(analyze_chunk_with_gpt4, chunk, prompt): chunk 
            for chunk in chunks
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_chunk):
            chunk = future_to_chunk[future]
            try:
                result = future.result()
                results.append(result)
                status = "✓" if result['success'] else "✗"
                print(f"{status} Chunk {result['chunk_index']} ({result['word_count']} words)")
            except Exception as e:
                print(f"✗ Chunk {chunk['chunk_index']} failed: {e}")
                results.append({
                    'chunk_index': chunk['chunk_index'],
                    'chunk_text': chunk['chunk_text'],
                    'analysis': f"Processing error: {str(e)}",
                    'word_count': chunk['word_count'],
                    'success': False
                })
    
    # Sort results by chunk_index to maintain order
    results.sort(key=lambda x: x['chunk_index'])
    return results

def save_partials(results: List[Dict[str, Any]], output_dir: str) -> None:
    """Save analysis results as individual JSON files."""
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    for result in results:
        filename = f"chunk_{result['chunk_index']:02d}.json"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"Saved: {filepath}")

def main():
    """Main entry point for command line usage."""
    if len(sys.argv) < 2:
        print("Usage: python analyze_chunk.py <transcript_file> [output_dir]")
        print("Example: python analyze_chunk.py data/transcripts/sample_transcript.txt data/partials/sample")
        sys.exit(1)
    
    transcript_file = sys.argv[1]
    
    # Default output directory based on transcript filename
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    else:
        # Extract base name from transcript file
        base_name = Path(transcript_file).stem.replace('_transcript', '')
        output_dir = f"data/partials/{base_name}"
    
    try:
        # Validate OpenAI API key early
        print("Validating OpenAI API key...")
        validate_openai_api_key()
        print("✓ OpenAI API key validated")
        
        print(f"Loading transcript: {transcript_file}")
        transcript_content = load_transcript(transcript_file)
        
        print("Extracting segments...")
        segments = extract_segments_from_transcript(transcript_content)
        print(f"Found {len(segments)} segments")
        
        if not segments:
            raise ValueError("No timestamped segments found in transcript. Please check the transcript format.")
        
        print("Creating intelligent chunks...")
        chunks = create_intelligent_chunks(segments, target_words=1200)
        print(f"Created {len(chunks)} chunks")
        
        if not chunks:
            raise ValueError("No chunks created. Transcript may be too short or improperly formatted.")
        
        # Show chunk summary
        for chunk in chunks:
            print(f"  Chunk {chunk['chunk_index']}: {chunk['word_count']} words")
        
        print("Loading analysis prompt...")
        prompt = load_analysis_prompt()
        
        print("Starting parallel analysis...")
        results = process_chunks_parallel(chunks, prompt, max_workers=4)
        
        print(f"Saving results to: {output_dir}")
        save_partials(results, output_dir)
        
        # Summary
        successful = sum(1 for r in results if r['success'])
        total = len(results)
        print(f"\nCompleted: {successful}/{total} chunks processed successfully")
        
        if successful < total:
            print("⚠️  Some chunks failed. Check the output files for error details.")
            failed_chunks = [r['chunk_index'] for r in results if not r['success']]
            print(f"Failed chunks: {failed_chunks}")
        else:
            print("✓ All chunks processed successfully!")
            
    except ValueError as e:
        print(f"✗ Validation Error: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"✗ File Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()