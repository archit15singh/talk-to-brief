#!/usr/bin/env python3
"""
Brief generation and merging script.
Combines partial analyses into final brief.md output using GPT-4 for intelligent merging.
"""

import os
import sys
import json
import glob
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from openai import OpenAI
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

def load_partials(partials_dir: str) -> List[Dict[str, Any]]:
    """Load all partial analysis files from directory."""
    partial_files = glob.glob(f"{partials_dir}/chunk_*.json")
    partial_files.sort()  # Ensure correct order
    
    partials = []
    for file_path in partial_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                partial = json.load(f)
                if partial.get('success', False):
                    partials.append(partial)
                else:
                    print(f"Warning: Skipping failed chunk: {file_path}")
        except Exception as e:
            print(f"Warning: Could not load {file_path}: {e}")
    
    return partials

def extract_sections_from_analysis(analysis: str) -> Dict[str, str]:
    """Extract structured sections from GPT-4 analysis."""
    sections = {
        'approach_script': '',
        'questions': '',
        'timeline': '',
        'claims_assumptions_tradeoffs': ''
    }
    
    lines = analysis.split('\n')
    current_section = None
    current_content = []
    
    for line in lines:
        line = line.strip()
        
        # Detect section headers
        if '**Approach Script' in line or 'Approach Script' in line:
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = 'approach_script'
            current_content = []
        elif 'Five High-Signal Questions' in line or 'Questions' in line:
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = 'questions'
            current_content = []
        elif 'Timeline Highlights' in line:
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = 'timeline'
            current_content = []
        elif 'Key Claims, Assumptions, Trade-offs' in line or 'Claims, Assumptions' in line:
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = 'claims_assumptions_tradeoffs'
            current_content = []
        elif current_section and line:
            current_content.append(line)
    
    # Don't forget the last section
    if current_section:
        sections[current_section] = '\n'.join(current_content).strip()
    
    return sections

def merge_partials_to_brief(partials_dir: str, output_path: str) -> bool:
    """Merge partial analyses into a comprehensive brief using GPT-4."""
    try:
        print(f"Loading partials from: {partials_dir}")
        partials = load_partials(partials_dir)
        
        if not partials:
            print("Error: No successful partial analyses found")
            return False
        
        print(f"Found {len(partials)} successful partial analyses")
        
        # Collect all analyses for GPT-4 merging
        all_analyses = []
        total_words = 0
        
        for i, partial in enumerate(partials):
            chunk_index = partial.get('chunk_index', i)
            analysis = partial.get('analysis', '')
            word_count = partial.get('word_count', 0)
            total_words += word_count
            
            all_analyses.append(f"=== CHUNK {chunk_index + 1} ANALYSIS ===\n{analysis}")
        
        # Use GPT-4 to intelligently merge the analyses
        print("Merging analyses using GPT-4...")
        merged_analysis = merge_with_gpt4(all_analyses)
        
        if not merged_analysis:
            print("Error: Failed to merge analyses with GPT-4")
            return False
        
        # Generate the final brief
        brief_content = generate_final_brief_from_merged(
            merged_analysis,
            len(partials),
            total_words
        )
        
        # Save the brief
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(brief_content)
        
        print(f"Brief generated successfully: {output_path}")
        return True
        
    except Exception as e:
        print(f"Error generating brief: {e}")
        return False

def merge_with_gpt4(analyses: List[str]) -> str:
    """Use GPT-4 to intelligently merge multiple partial analyses, with fallback to rule-based merging."""
    try:
        # Validate OpenAI API key
        try:
            api_key = validate_openai_api_key()
        except ValueError as e:
            print(f"Warning: {e}, falling back to rule-based merging")
            return merge_with_rules(analyses)
        
        client = OpenAI(api_key=api_key)
        
        # Load merge prompt - try multiple paths
        merge_prompt_paths = [
            "config/merge.md",  # When run from src/
            "src/config/merge.md",  # When run from root
            Path(__file__).parent / "config" / "merge.md"  # Relative to this file
        ]
        
        merge_instructions = None
        for path in merge_prompt_paths:
            if Path(path).exists():
                with open(path, 'r', encoding='utf-8') as f:
                    merge_instructions = f.read()
                break
        
        if not merge_instructions:
            merge_instructions = """
You have multiple partial outputs from different segments of the same talk. Merge them into ONE final output with the same four sections:

## 1) Approach Script (3 sentences)
## 2) Five High-Signal Questions (≤ 2 lines each, each tied to a timestamp)
## 3) Timeline Highlights (8–12 bullets, chronological, no duplicates)
## 4) Key Claims, Assumptions, Trade-offs (deduplicated, concise lists)

## Instructions:
- Deduplicate overlapping items.
- Preserve timestamps; if duplicates have same timestamp, merge wording.
- Keep total output under 800 words.
- Ensure sections flow naturally as if it came from one continuous talk.
- Return clean markdown-formatted text.
"""
        
        # Combine all analyses
        combined_input = "\n\n".join(analyses)
        
        # Create the prompt
        prompt = f"{merge_instructions}\n\n{combined_input}"
        
        print("Calling GPT-4 for intelligent merging...")
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert at synthesizing and merging content analysis. Follow the instructions precisely."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.3,
                timeout=90  # 90 second timeout for merge operations
            )
        except openai.RateLimitError as e:
            print(f"Warning: OpenAI rate limit exceeded ({e}), falling back to rule-based merging")
            return merge_with_rules(analyses)
        except openai.APIError as e:
            print(f"Warning: OpenAI API error ({e}), falling back to rule-based merging")
            return merge_with_rules(analyses)
        except openai.AuthenticationError as e:
            print(f"Warning: OpenAI authentication failed ({e}), falling back to rule-based merging")
            return merge_with_rules(analyses)
        except Exception as e:
            print(f"Warning: OpenAI request failed ({e}), falling back to rule-based merging")
            return merge_with_rules(analyses)
        
        merged_content = response.choices[0].message.content.strip()
        print("GPT-4 merging completed successfully")
        return merged_content
        
    except Exception as e:
        print(f"Error in GPT-4 merging: {e}, falling back to rule-based merging")
        return merge_with_rules(analyses)

def merge_with_rules(analyses: List[str]) -> str:
    """Rule-based merging as fallback when GPT-4 is not available."""
    print("Using rule-based merging...")
    
    # Parse all analyses to extract sections
    all_sections = []
    for analysis in analyses:
        sections = extract_sections_from_analysis(analysis.split("===")[2] if "===" in analysis else analysis)
        all_sections.append(sections)
    
    # Merge approach scripts (take the first non-empty one and enhance it)
    approach_script = ""
    for sections in all_sections:
        if sections['approach_script'] and not approach_script:
            approach_script = sections['approach_script']
            break
    
    # Collect and deduplicate questions
    all_questions = []
    for sections in all_sections:
        if sections['questions']:
            questions_text = sections['questions']
            # Split by lines and filter out section headers
            for line in questions_text.split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('**') and '?' in line:
                    if line not in all_questions:
                        all_questions.append(line)
    
    # Collect and sort timeline items
    all_timeline_items = []
    for sections in all_sections:
        if sections['timeline']:
            timeline_text = sections['timeline']
            for line in timeline_text.split('\n'):
                line = line.strip()
                if line and line.startswith('-') and '[' in line and ']' in line:
                    if line not in all_timeline_items:
                        all_timeline_items.append(line)
    
    # Sort timeline items by timestamp
    def extract_timestamp(item):
        try:
            # Extract timestamp like [00:14 -> 00:22] or [09:15]
            import re
            match = re.search(r'\[(\d{2}):(\d{2})', item)
            if match:
                minutes, seconds = match.groups()
                return int(minutes) * 60 + int(seconds)
            return 0
        except:
            return 0
    
    all_timeline_items.sort(key=extract_timestamp)
    
    # Collect claims, assumptions, trade-offs
    all_claims = []
    all_assumptions = []
    all_tradeoffs = []
    
    for sections in all_sections:
        if sections['claims_assumptions_tradeoffs']:
            text = sections['claims_assumptions_tradeoffs']
            lines = text.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if 'Claims' in line or 'assertions' in line:
                    current_section = 'claims'
                elif 'Assumptions' in line or 'constraints' in line:
                    current_section = 'assumptions'
                elif 'Trade-offs' in line or 'gains vs' in line:
                    current_section = 'tradeoffs'
                elif line and line.startswith('-') and current_section:
                    if current_section == 'claims' and line not in all_claims:
                        all_claims.append(line)
                    elif current_section == 'assumptions' and line not in all_assumptions:
                        all_assumptions.append(line)
                    elif current_section == 'tradeoffs' and line not in all_tradeoffs:
                        all_tradeoffs.append(line)
    
    # Format the merged output
    merged_output = f"""## Approach Script

{approach_script}

## Five High-Signal Questions

{chr(10).join(all_questions[:5])}

## Timeline Highlights

{chr(10).join(all_timeline_items[:12])}

## Key Claims, Assumptions, Trade-offs

**Claims:**
{chr(10).join(all_claims)}

**Assumptions:**
{chr(10).join(all_assumptions)}

**Trade-offs:**
{chr(10).join(all_tradeoffs)}"""
    
    return merged_output

def generate_final_brief_from_merged(merged_analysis: str, chunk_count: int, total_words: int) -> str:
    """Generate the final brief markdown content from merged analysis."""
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    brief = f"""# Audio Brief

Generated: {timestamp}
Source: {chunk_count} chunks, {total_words} words total

## Executive Summary

This brief synthesizes key insights from the analyzed audio content, providing actionable conversation starters, strategic questions, and critical decision points.

{merged_analysis}

---

*Generated by Audio Brief Generator Pipeline*
"""
    
    return brief

def main():
    """Main entry point for brief generation."""
    if len(sys.argv) < 3:
        print("Usage: python merge_brief.py <partials_dir> <output_path>")
        print("Example: python merge_brief.py data/partials/sample data/outputs/sample_brief.md")
        sys.exit(1)
    
    partials_dir = sys.argv[1]
    output_path = sys.argv[2]
    
    try:
        # Validate inputs
        if not os.path.exists(partials_dir):
            raise FileNotFoundError(f"Partials directory not found: {partials_dir}")
        
        if not os.path.isdir(partials_dir):
            raise ValueError(f"Path is not a directory: {partials_dir}")
        
        # Check if there are any partial files
        partial_files = glob.glob(f"{partials_dir}/chunk_*.json")
        if not partial_files:
            raise ValueError(f"No chunk files found in directory: {partials_dir}")
        
        print(f"Found {len(partial_files)} partial files to merge")
        
        success = merge_partials_to_brief(partials_dir, output_path)
        
        if success:
            print("✓ Brief generation completed successfully!")
            sys.exit(0)
        else:
            print("✗ Brief generation failed")
            sys.exit(1)
            
    except FileNotFoundError as e:
        print(f"✗ File Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"✗ Validation Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()