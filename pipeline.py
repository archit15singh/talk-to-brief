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
from prompts import PromptTemplates
from schemas import QuestionPipelineSchemas

# Load environment variables from .env file
load_dotenv()

# ---------- CONFIG ----------
INPUT_TXT = "data/transcripts/building-scalable-apis.md"  # path to your transcript
BUFFER_SIZE = 3             # sentences in rolling window
BREAKPOINT_THRESHOLD = 92   # higher = fewer/larger chunks

# Data hierarchy structure
DATA_ROOT = Path("data")
PROCESSED_ROOT = DATA_ROOT / "processed"

class QuestionGenerationPipeline:
    """3-step pipeline for generating high-leverage audience questions"""
    
    def __init__(self, client: OpenAIClient = None):
        self.client = client or OpenAIClient()
        self.config = CompletionConfig(model=ModelType.GPT_4O_MINI, temperature=0.3)
        self.schemas = QuestionPipelineSchemas()
        self.prompts = PromptTemplates()
    
    def step1_summarization(self, chunk: str):
        """Step 1: Create structured summary with main points, evidence, assumptions, open loops"""
        messages = [
            ChatMessage("system", self.prompts.SUMMARIZATION_SYSTEM),
            ChatMessage("user", self.prompts.SUMMARIZATION_PROMPT.format(chunk=chunk))
        ]
        
        return self.client.structured_completion(
            messages=messages,
            schema=self.schemas.summarization_schema(),
            schema_name="SummarizationOutput",
            config=self.config
        )
    
    def step2_critical_thinking(self, summary):
        """Step 2: Identify weak spots, contrarian angles, future implications, hooks"""
        summary_text = self._format_summary_for_analysis(summary)
        
        messages = [
            ChatMessage("system", self.prompts.CRITICAL_THINKING_SYSTEM),
            ChatMessage("user", self.prompts.CRITICAL_THINKING_PROMPT.format(summary=summary_text))
        ]
        
        return self.client.structured_completion(
            messages=messages,
            schema=self.schemas.critical_thinking_schema(),
            schema_name="CriticalThinkingOutput",
            config=self.config
        )
    
    def step3_question_generation(self, critical_analysis):
        """Step 3: Generate and rank 8-10 high-leverage questions"""
        analysis_text = self._format_critical_analysis(critical_analysis)
        
        messages = [
            ChatMessage("system", self.prompts.QUESTION_GENERATION_SYSTEM),
            ChatMessage("user", self.prompts.QUESTION_GENERATION_PROMPT.format(critical_analysis=analysis_text))
        ]
        
        return self.client.structured_completion(
            messages=messages,
            schema=self.schemas.question_generation_schema(),
            schema_name="QuestionGenerationOutput",
            config=self.config
        )
    
    def merge_final_questions(self, all_question_sets):
        """Final step: Merge and deduplicate into top 5 questions"""
        questions_text = self._format_all_questions(all_question_sets)
        
        messages = [
            ChatMessage("system", self.prompts.MERGE_QUESTIONS_SYSTEM),
            ChatMessage("user", self.prompts.MERGE_QUESTIONS_PROMPT.format(all_questions=questions_text))
        ]
        
        return self.client.structured_completion(
            messages=messages,
            schema=self.schemas.final_questions_schema(),
            schema_name="FinalQuestionsOutput",
            config=self.config
        )
    
    def process_chunk(self, chunk: str, chunk_number: int):
        """Process a single chunk through all 3 steps"""
        print(f"Processing chunk {chunk_number} through 3-step pipeline...")
        
        try:
            # Step 1: Summarization
            print(f"  Step 1: Summarization...")
            summary = self.step1_summarization(chunk)
            
            # Step 2: Critical Thinking
            print(f"  Step 2: Critical Thinking...")
            critical_analysis = self.step2_critical_thinking(summary)
            
            # Step 3: Question Generation
            print(f"  Step 3: Question Generation...")
            questions = self.step3_question_generation(critical_analysis)
            
            return {
                'chunk_number': chunk_number,
                'original_text': chunk,
                'summary': summary,
                'critical_analysis': critical_analysis,
                'questions': questions,
                'char_count': len(chunk)
            }
            
        except Exception as e:
            print(f"✗ Error processing chunk {chunk_number}: {e}")
            return {
                'chunk_number': chunk_number,
                'original_text': chunk,
                'error': str(e),
                'char_count': len(chunk)
            }
    
    def _format_summary_for_analysis(self, summary):
        """Format summary data for critical thinking step"""
        formatted = "STRUCTURED SUMMARY:\n\n"
        
        formatted += "Main Points:\n"
        for point in summary.get('main_points', []):
            formatted += f"• {point}\n"
        
        formatted += "\nEvidence:\n"
        for evidence_group in summary.get('evidence', []):
            formatted += f"• {evidence_group.get('point', 'Unknown point')}:\n"
            for item in evidence_group.get('evidence_items', []):
                formatted += f"  - {item}\n"
        
        formatted += "\nAssumptions:\n"
        for assumption in summary.get('assumptions', []):
            formatted += f"• {assumption}\n"
        
        formatted += "\nOpen Loops:\n"
        for loop in summary.get('open_loops', []):
            formatted += f"• {loop}\n"
        
        return formatted
    
    def _format_critical_analysis(self, analysis):
        """Format critical analysis for question generation"""
        formatted = "CRITICAL ANALYSIS:\n\n"
        
        formatted += "Weak Spots:\n"
        for spot in analysis.get('weak_spots', []):
            formatted += f"• {spot}\n"
        
        formatted += "\nContrarian Angles:\n"
        for angle in analysis.get('contrarian_angles', []):
            formatted += f"• {angle}\n"
        
        formatted += "\nFuture Implications:\n"
        for implication in analysis.get('future_implications', []):
            formatted += f"• {implication}\n"
        
        formatted += "\nHooks:\n"
        for hook in analysis.get('hooks', []):
            formatted += f"• {hook}\n"
        
        return formatted
    
    def _format_all_questions(self, question_sets):
        """Format all question sets for final merging"""
        formatted = "ALL QUESTION SETS:\n\n"
        
        for q_set in question_sets:
            if 'error' in q_set:
                continue
                
            formatted += f"Chunk {q_set['chunk_number']} Questions:\n"
            questions = q_set.get('questions', {}).get('questions', [])
            
            for q in questions:
                rank = q.get('rank', 0)
                question = q.get('question', 'No question')
                reason = q.get('leverage_reason', 'No reason')
                formatted += f"[{rank}] {question} → {reason}\n"
            
            formatted += "\n"
        
        return formatted

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

def process_chunks_with_questions(chunks, dirs):
    """Process chunks through 3-step question generation pipeline."""
    pipeline = QuestionGenerationPipeline()
    
    results = []
    
    print("\n" + "=" * 60)
    print("3-STEP QUESTION GENERATION PIPELINE:")
    print("=" * 60)
    print("Step 1: Summarization Layer")
    print("Step 2: Critical Thinking Layer") 
    print("Step 3: Question Generation & Ranking")
    print("=" * 60)
    
    # Process each chunk through the 3-step pipeline
    for i, chunk in enumerate(chunks, 1):
        print(f"\n--- Processing Chunk {i}/{len(chunks)} ---")
        result = pipeline.process_chunk(chunk, i)
        results.append(result)
        
        if 'error' not in result:
            questions_count = len(result.get('questions', {}).get('questions', []))
            print(f"✓ Chunk {i} complete: {questions_count} questions generated")
        else:
            print(f"✗ Chunk {i} failed: {result['error']}")
    
    # Merge all questions into final top 5
    print(f"\n--- Final Merge: Top 5 Questions ---")
    successful_results = [r for r in results if 'error' not in r]
    
    if successful_results:
        try:
            final_questions = pipeline.merge_final_questions(successful_results)
            print(f"✓ Final merge complete: {len(final_questions.get('top_questions', []))} top questions")
        except Exception as e:
            print(f"✗ Final merge failed: {e}")
            final_questions = {'top_questions': [], 'error': str(e)}
    else:
        print("✗ No successful chunks to merge")
        final_questions = {'top_questions': [], 'error': 'No successful chunks'}
    
    # Save all artifacts
    questions_dir, final_file, final_readable = save_question_pipeline_results(dirs, results, final_questions)
    print(f"✓ Saved question pipeline artifacts: {questions_dir}")
    print(f"  Final questions: {final_readable}")
    
    return results, final_questions

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
        
        # Process chunks through 3-step question generation pipeline
        results, final_questions = process_chunks_with_questions(chunks, dirs)
        
        # Save overall processing metadata
        config = {
            'input_file': INPUT_TXT,
            'buffer_size': BUFFER_SIZE,
            'breakpoint_threshold': BREAKPOINT_THRESHOLD,
            'model': 'gpt-4o-mini'
        }
        
        stats = {
            'total_chunks': len(chunks),
            'total_results': len(results),
            'successful_chunks': len([r for r in results if 'error' not in r]),
            'final_questions_count': len(final_questions.get('top_questions', [])),
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
        print(f"├── 03_summaries/   - Legacy summaries (deprecated)")
        print(f"├── 04_questions/   - 3-step question analysis")
        print(f"└── metadata/       - Processing metadata")
        
        print("\n" + "=" * 40)
        print("FINAL RESULTS:")
        print("=" * 40)
        
        # Show final top questions
        top_questions = final_questions.get('top_questions', [])
        if top_questions:
            print(f"\n🎯 TOP {len(top_questions)} HIGH-LEVERAGE QUESTIONS:")
            for q in top_questions:
                rank = q.get('rank', 0)
                question = q.get('question', 'No question')
                reason = q.get('leverage_reason', 'No reason')
                print(f"\n{rank}. {question}")
                print(f"   💡 {reason}")
        else:
            print("\n❌ No final questions generated")
        
        successful_chunks = len([r for r in results if 'error' not in r])
        print(f"\n📊 Pipeline Stats:")
        print(f"   • {successful_chunks}/{len(chunks)} chunks processed successfully")
        print(f"   • {len(top_questions)} final high-leverage questions")
        print(f"   • Full analysis saved in: {dirs['base']}/04_questions/")
        
        # Return processing results and directory info
        return {
            'chunks': chunks,
            'results': results,
            'final_questions': final_questions,
            'dirs': dirs,
            'stats': stats
        }
    else:
        print("Failed to process transcript.")
        return None

if __name__ == "__main__":
    main()