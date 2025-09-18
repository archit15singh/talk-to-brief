#!/usr/bin/env python3
"""
Main pipeline orchestration and user interface
"""

import time
from pathlib import Path

# Import configuration
from config.settings import INPUT_TXT, BUFFER_SIZE, BREAKPOINT_THRESHOLD, MIN_CHUNK_SIZE, MAX_CHUNK_SIZE, OVERLAP_SIZE

# Import services and utilities
from processors.text_processor import load_and_chunk_transcript
from services.orchestrator import process_chunks_with_questions
from file_manager import create_processing_directories, save_processing_metadata
from utils.logger import Logger

# Global logger instance
log = Logger()

def main():
    """Main pipeline function with full artifact tracking."""
    pipeline_start = time.time()
    
    log.header("SEMANTIC TRANSCRIPT ANALYSIS & QUESTION GENERATION")
    
    # Show configuration
    log.info(f"Input transcript: {log._colorize(INPUT_TXT, 'CYAN')}")
    log.info(f"Semantic chunking: {BUFFER_SIZE} sentence buffer, {BREAKPOINT_THRESHOLD}% threshold")
    log.info(f"AI Model: {log._colorize('GPT-5-Nano', 'MAGENTA')}")
    
    # Create processing directories
    transcript_name = Path(INPUT_TXT).name
    dirs = create_processing_directories(transcript_name)
    log.success(f"Initialized workspace: {dirs['base']}")
    
    # Process transcript with artifact saving
    log.subheader("Text Processing & Semantic Chunking")
    chunks, clean_text, cleaning_stats = load_and_chunk_transcript(
        INPUT_TXT, dirs, BUFFER_SIZE, BREAKPOINT_THRESHOLD, 
        MIN_CHUNK_SIZE, MAX_CHUNK_SIZE, OVERLAP_SIZE
    )
    
    if chunks:
        log.success(f"Transcript processed into {len(chunks)} semantic chunks")
        
        # Process chunks through 3-step question generation pipeline
        results, final_questions = process_chunks_with_questions(chunks, dirs)
        
        # Save overall processing metadata
        config = {
            'input_file': INPUT_TXT,
            'buffer_size': BUFFER_SIZE,
            'breakpoint_threshold': BREAKPOINT_THRESHOLD,
            'model': 'gpt-5-nano',
            'pipeline_version': '3-step-v1.0'
        }
        
        stats = {
            'total_chunks': len(chunks),
            'total_results': len(results),
            'successful_chunks': len([r for r in results if 'error' not in r]),
            'final_questions_count': len(final_questions.get('top_questions', [])),
            'cleaning_stats': cleaning_stats,
            'avg_chunk_size': sum(len(c) for c in chunks) / len(chunks) if chunks else 0,
            'total_processing_time': time.time() - pipeline_start
        }
        
        metadata_file = save_processing_metadata(dirs, config, stats)
        log.file_saved(metadata_file, "Pipeline configuration and statistics")
        
        # Show final results
        log.header("PIPELINE COMPLETE")
        
        # Directory structure
        structure_items = [
            ("01_cleaned/", "Cleaned transcript text"),
            (f"02_chunks/", f"{len(chunks)} semantic chunks"),
            ("03_summaries/", "Legacy summaries (deprecated)"),
            ("04_questions/", "3-step question analysis"),
            ("metadata/", "Processing metadata & config")
        ]
        log.directory_tree(dirs['base'], structure_items)
        
        # Show final top questions
        log.subheader("High-Leverage Questions Generated")
        top_questions = final_questions.get('top_questions', [])
        
        if top_questions:
            log.success(f"Generated {len(top_questions)} high-leverage questions")
            
            for q in top_questions:
                rank = q.get('rank', 0)
                question = q.get('question', 'No question')
                reason = q.get('leverage_reason', 'No reason')
                log.question_preview(rank, question, reason)
        else:
            log.error("No final questions generated")
        
        # Final statistics
        log.subheader("Pipeline Statistics")
        successful_chunks = len([r for r in results if 'error' not in r])
        success_rate = (successful_chunks / len(chunks)) * 100
        
        log.metric("Chunks processed", f"{successful_chunks}/{len(chunks)}", color='GREEN')
        log.metric("Success rate", f"{success_rate:.1f}%", color='GREEN')
        log.metric("Questions generated", len(top_questions), color='MAGENTA')
        log.metric("Average chunk size", f"{stats['avg_chunk_size']:.0f}", " chars")
        log.processing_time(pipeline_start, "Complete pipeline")
        
        log.info(f"Full analysis available at: {log._colorize(str(dirs['base'] / '04_questions'), 'CYAN')}")
        
        # Return processing results and directory info
        return {
            'chunks': chunks,
            'results': results,
            'final_questions': final_questions,
            'dirs': dirs,
            'stats': stats
        }
    else:
        log.error("Failed to process transcript")
        return None

if __name__ == "__main__":
    main()