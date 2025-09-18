#!/usr/bin/env python3
"""
Data access and persistence layer for file operations
"""

import json
import os
from pathlib import Path
from datetime import datetime
from utils.logger import Logger

# Global logger instance
log = Logger()

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
    for name, dir_path in dirs.items():
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            if name != 'base':  # Don't log the base directory separately
                log.success(f"Created {name} directory", indent=1)
        except Exception as e:
            log.error(f"Failed to create {name} directory: {e}", indent=1)
            raise
    
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

def save_question_pipeline_results(dirs, results, final_questions):
    """Save all question pipeline artifacts"""
    
    # Create question pipeline directory
    questions_dir = dirs['base'] / "04_questions"
    questions_dir.mkdir(exist_ok=True)
    
    # Save individual chunk results
    for result in results:
        if 'error' in result:
            continue
            
        chunk_num = result['chunk_number']
        
        # Save detailed analysis
        analysis_file = questions_dir / f"analysis_{chunk_num:03d}.json"
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        # Save human-readable summary
        readable_file = questions_dir / f"readable_{chunk_num:03d}.md"
        with open(readable_file, 'w', encoding='utf-8') as f:
            f.write(f"# Analysis for Chunk {chunk_num}\n\n")
            
            if 'summary' in result:
                f.write("## Structured Summary\n\n")
                summary = result['summary']
                
                f.write("### Main Points\n")
                for point in summary.get('main_points', []):
                    f.write(f"• {point}\n")
                
                f.write("\n### Evidence\n")
                for evidence_group in summary.get('evidence', []):
                    f.write(f"• **{evidence_group.get('point', 'Unknown')}:**\n")
                    for item in evidence_group.get('evidence_items', []):
                        f.write(f"  - {item}\n")
                
                f.write("\n### Assumptions\n")
                for assumption in summary.get('assumptions', []):
                    f.write(f"• {assumption}\n")
                
                f.write("\n### Open Loops\n")
                for loop in summary.get('open_loops', []):
                    f.write(f"• {loop}\n")
            
            if 'critical_analysis' in result:
                f.write("\n## Critical Analysis\n\n")
                analysis = result['critical_analysis']
                
                f.write("### Weak Spots\n")
                for spot in analysis.get('weak_spots', []):
                    f.write(f"• {spot}\n")
                
                f.write("\n### Contrarian Angles\n")
                for angle in analysis.get('contrarian_angles', []):
                    f.write(f"• {angle}\n")
                
                f.write("\n### Future Implications\n")
                for implication in analysis.get('future_implications', []):
                    f.write(f"• {implication}\n")
                
                f.write("\n### Hooks\n")
                for hook in analysis.get('hooks', []):
                    f.write(f"• {hook}\n")
            
            if 'questions' in result:
                f.write("\n## Generated Questions\n\n")
                questions = result['questions'].get('questions', [])
                
                # Sort by rank (higher is better)
                sorted_questions = sorted(questions, key=lambda x: x.get('rank', 0), reverse=True)
                
                for q in sorted_questions:
                    rank = q.get('rank', 0)
                    question = q.get('question', 'No question')
                    reason = q.get('leverage_reason', 'No reason')
                    f.write(f"**[{rank}]** {question}\n")
                    f.write(f"*Leverage: {reason}*\n\n")
    
    # Save final top 5 questions
    final_file = questions_dir / "final_top5_questions.json"
    with open(final_file, 'w', encoding='utf-8') as f:
        json.dump(final_questions, f, indent=2, ensure_ascii=False)
    
    # Save human-readable final questions
    final_readable = questions_dir / "final_top5_questions.md"
    with open(final_readable, 'w', encoding='utf-8') as f:
        f.write("# Top 5 High-Leverage Questions\n\n")
        f.write(f"*Generated: {datetime.now().isoformat()}*\n\n")
        
        top_questions = final_questions.get('top_questions', [])
        for q in top_questions:
            rank = q.get('rank', 0)
            question = q.get('question', 'No question')
            reason = q.get('leverage_reason', 'No reason')
            f.write(f"## {rank}. {question}\n\n")
            f.write(f"**Why this creates leverage:** {reason}\n\n")
    
    # Save processing index
    index_file = questions_dir / "question_pipeline_index.json"
    pipeline_index = {
        'total_chunks_processed': len([r for r in results if 'error' not in r]),
        'total_chunks_failed': len([r for r in results if 'error' in r]),
        'final_questions_count': len(final_questions.get('top_questions', [])),
        'processing_timestamp': datetime.now().isoformat(),
        'pipeline_version': '3-step-v1.0'
    }
    
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(pipeline_index, f, indent=2)
    
    return questions_dir, final_file, final_readable