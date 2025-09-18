#!/usr/bin/env python3
"""
High-level orchestration and business logic
"""

import time
from services.question_pipeline import QuestionGenerationPipeline
from data.file_manager import save_question_pipeline_results
from utils.logger import Logger

# Global logger instance
log = Logger()

def process_chunks_with_questions(chunks, dirs):
    """Process chunks through 3-step question generation pipeline."""
    start_time = time.time()
    pipeline = QuestionGenerationPipeline()
    results = []
    
    log.header("3-STEP QUESTION GENERATION PIPELINE")
    log.info("Step 1: Summarization Layer - Extract main points, evidence, assumptions")
    log.info("Step 2: Critical Thinking Layer - Identify weak spots, contrarian angles") 
    log.info("Step 3: Question Generation - Create high-leverage audience questions")
    
    log.subheader(f"Processing {len(chunks)} Chunks")
    
    # Process each chunk through the 3-step pipeline
    successful_count = 0
    failed_count = 0
    
    for i, chunk in enumerate(chunks, 1):
        log.progress(i-1, len(chunks), "chunk")
        
        result = pipeline.process_chunk(chunk, i)
        results.append(result)
        
        if 'error' not in result:
            successful_count += 1
            questions_count = len(result.get('questions', {}).get('questions', []))
            
            # Show preview of top question for this chunk
            if questions_count > 0:
                top_q = max(result['questions']['questions'], key=lambda x: x.get('rank', 0))
                log.info(f"Top question (rank {top_q.get('rank', 0)}): {top_q.get('question', 'N/A')[:60]}...", indent=3)
        else:
            failed_count += 1
    
    log.progress(len(chunks), len(chunks), "chunk")
    
    # Show processing summary
    log.subheader("Chunk Processing Summary")
    log.metric("Successful chunks", successful_count, color='GREEN')
    log.metric("Failed chunks", failed_count, color='RED' if failed_count > 0 else 'GREEN')
    log.metric("Success rate", f"{(successful_count/len(chunks)*100):.1f}%", color='GREEN')
    
    # Merge all questions into final top 5
    log.subheader("Final Question Synthesis")
    successful_results = [r for r in results if 'error' not in r]
    
    if successful_results:
        try:
            merge_start = time.time()
            log.info("Merging and ranking questions from all chunks...")
            
            final_questions = pipeline.merge_final_questions(successful_results)
            final_count = len(final_questions.get('top_questions', []))
            
            log.success(f"Synthesized {final_count} top questions from {len(successful_results)} chunks")
            log.processing_time(merge_start, "Question synthesis")
            
        except Exception as e:
            log.error(f"Final merge failed: {e}")
            final_questions = {'top_questions': [], 'error': str(e)}
    else:
        log.error("No successful chunks to merge")
        final_questions = {'top_questions': [], 'error': 'No successful chunks'}
    
    # Save all artifacts
    log.subheader("Saving Artifacts")
    questions_dir, final_file, final_readable = save_question_pipeline_results(dirs, results, final_questions)
    
    log.file_saved(questions_dir, "Question analysis directory")
    log.file_saved(final_readable, "Human-readable final questions")
    log.file_saved(final_file, "Machine-readable final questions (JSON)")
    
    log.processing_time(start_time, "Complete question generation pipeline")
    
    return results, final_questions