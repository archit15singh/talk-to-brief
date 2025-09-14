#!/usr/bin/env python3
"""
Brief generation and merging script.
Combines partial analyses into final brief.md output.
"""

import os
import sys
import json
import glob
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

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
    """Merge partial analyses into a comprehensive brief."""
    try:
        print(f"Loading partials from: {partials_dir}")
        partials = load_partials(partials_dir)
        
        if not partials:
            print("Error: No successful partial analyses found")
            return False
        
        print(f"Found {len(partials)} successful partial analyses")
        
        # Extract and organize content
        all_approach_scripts = []
        all_questions = []
        all_timeline_items = []
        all_claims = []
        all_assumptions = []
        all_tradeoffs = []
        
        total_words = 0
        
        for i, partial in enumerate(partials):
            chunk_index = partial.get('chunk_index', i)
            analysis = partial.get('analysis', '')
            word_count = partial.get('word_count', 0)
            total_words += word_count
            
            sections = extract_sections_from_analysis(analysis)
            
            # Collect approach scripts
            if sections['approach_script']:
                all_approach_scripts.append(f"**Chunk {chunk_index + 1}:** {sections['approach_script']}")
            
            # Collect questions
            if sections['questions']:
                all_questions.append(f"### From Chunk {chunk_index + 1}:\n{sections['questions']}")
            
            # Collect timeline items
            if sections['timeline']:
                all_timeline_items.append(sections['timeline'])
            
            # Collect claims, assumptions, tradeoffs
            if sections['claims_assumptions_tradeoffs']:
                all_claims.append(f"### Chunk {chunk_index + 1}:\n{sections['claims_assumptions_tradeoffs']}")
        
        # Generate the final brief
        brief_content = generate_final_brief(
            all_approach_scripts,
            all_questions,
            all_timeline_items,
            all_claims,
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

def generate_final_brief(approach_scripts: List[str], questions: List[str], 
                        timeline_items: List[str], claims: List[str],
                        chunk_count: int, total_words: int) -> str:
    """Generate the final brief markdown content."""
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    brief = f"""# Audio Brief

Generated: {timestamp}
Source: {chunk_count} chunks, {total_words} words total

## Executive Summary

This brief synthesizes key insights from the analyzed audio content, providing actionable conversation starters, strategic questions, and critical decision points.

## Approach Scripts

These are conversation starters referencing specific moments from the content:

{chr(10).join(approach_scripts)}

## Strategic Questions

High-signal questions tied to specific claims and timestamps:

{chr(10).join(questions)}

## Timeline Highlights

Key moments and developments in chronological order:

{chr(10).join(timeline_items)}

## Claims, Assumptions & Trade-offs

Critical assertions, underlying assumptions, and strategic trade-offs identified:

{chr(10).join(claims)}

---

*Generated by Audio Brief Generator Pipeline*
"""
    
    return brief

def main():
    """Main entry point for brief generation."""
    if len(sys.argv) < 3:
        print("Usage: python merge_brief.py <partials_dir> <output_path>")
        sys.exit(1)
    
    partials_dir = sys.argv[1]
    output_path = sys.argv[2]
    
    success = merge_partials_to_brief(partials_dir, output_path)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()