#!/usr/bin/env python3
"""
Pipeline script for semantic chunking of transcript files using llama-index.
"""

import re
import os
import json
import time
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

# Advanced chunking config
MIN_CHUNK_SIZE = 500        # minimum characters per chunk
MAX_CHUNK_SIZE = 3000       # maximum characters per chunk
OVERLAP_SIZE = 100          # character overlap between chunks

# Data hierarchy structure
DATA_ROOT = Path("data")
PROCESSED_ROOT = DATA_ROOT / "processed"

# Enhanced logging utilities
class Logger:
    """Enhanced logging with colors and formatting"""
    
    # ANSI color codes
    COLORS = {
        'RESET': '\033[0m',
        'BOLD': '\033[1m',
        'DIM': '\033[2m',
        'RED': '\033[91m',
        'GREEN': '\033[92m',
        'YELLOW': '\033[93m',
        'BLUE': '\033[94m',
        'MAGENTA': '\033[95m',
        'CYAN': '\033[96m',
        'WHITE': '\033[97m',
        'GRAY': '\033[90m'
    }
    
    @classmethod
    def _colorize(cls, text, color):
        """Add color to text"""
        return f"{cls.COLORS.get(color, '')}{text}{cls.COLORS['RESET']}"
    
    @classmethod
    def header(cls, text, width=80):
        """Print a styled header"""
        border = "═" * width
        print(f"\n{cls._colorize(border, 'CYAN')}")
        print(f"{cls._colorize(text.center(width), 'CYAN')}")
        print(f"{cls._colorize(border, 'CYAN')}")
    
    @classmethod
    def subheader(cls, text, width=60):
        """Print a styled subheader"""
        border = "─" * width
        print(f"\n{cls._colorize(border, 'BLUE')}")
        print(f"{cls._colorize(text.center(width), 'BLUE')}")
        print(f"{cls._colorize(border, 'BLUE')}")
    
    @classmethod
    def success(cls, message, indent=0):
        """Print success message"""
        prefix = "  " * indent
        print(f"{prefix}{cls._colorize('✓', 'GREEN')} {message}")
    
    @classmethod
    def error(cls, message, indent=0):
        """Print error message"""
        prefix = "  " * indent
        print(f"{prefix}{cls._colorize('✗', 'RED')} {cls._colorize(message, 'RED')}")
    
    @classmethod
    def warning(cls, message, indent=0):
        """Print warning message"""
        prefix = "  " * indent
        print(f"{prefix}{cls._colorize('⚠', 'YELLOW')} {cls._colorize(message, 'YELLOW')}")
    
    @classmethod
    def info(cls, message, indent=0):
        """Print info message"""
        prefix = "  " * indent
        print(f"{prefix}{cls._colorize('ℹ', 'BLUE')} {message}")
    
    @classmethod
    def step(cls, step_num, title, description=""):
        """Print step header"""
        step_text = f"STEP {step_num}: {title}"
        print(f"\n{cls._colorize('🔄', 'MAGENTA')} {cls._colorize(step_text, 'BOLD')}")
        if description:
            print(f"   {cls._colorize(description, 'DIM')}")
    
    @classmethod
    def progress(cls, current, total, item_name="item"):
        """Print progress indicator"""
        percentage = (current / total) * 100
        bar_length = 30
        filled_length = int(bar_length * current // total)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        
        print(f"\r{cls._colorize('📊', 'CYAN')} Progress: [{bar}] {percentage:.1f}% ({current}/{total} {item_name}s)", end='', flush=True)
        if current == total:
            print()  # New line when complete
    
    @classmethod
    def metric(cls, label, value, unit="", color='WHITE'):
        """Print a metric"""
        print(f"   {cls._colorize('•', 'GRAY')} {label}: {cls._colorize(f'{value}{unit}', color)}")
    
    @classmethod
    def file_saved(cls, filepath, description=""):
        """Print file saved message"""
        print(f"   {cls._colorize('💾', 'GREEN')} Saved: {cls._colorize(str(filepath), 'CYAN')}")
        if description:
            print(f"      {cls._colorize(description, 'DIM')}")
    
    @classmethod
    def processing_time(cls, start_time, operation="Operation"):
        """Print processing time"""
        elapsed = time.time() - start_time
        if elapsed < 60:
            time_str = f"{elapsed:.2f}s"
        else:
            minutes = int(elapsed // 60)
            seconds = elapsed % 60
            time_str = f"{minutes}m {seconds:.1f}s"
        
        print(f"   {cls._colorize('⏱', 'YELLOW')} {operation} completed in {cls._colorize(time_str, 'BOLD')}")
    
    @classmethod
    def question_preview(cls, rank, question, reason, max_length=80):
        """Print a formatted question preview"""
        # Truncate question if too long
        if len(question) > max_length:
            question = question[:max_length-3] + "..."
        
        print(f"\n{cls._colorize(f'{rank}.', 'BOLD')} {cls._colorize(question, 'WHITE')}")
        print(f"   {cls._colorize('💡', 'YELLOW')} {cls._colorize(reason, 'DIM')}")
    
    @classmethod
    def directory_tree(cls, base_path, items):
        """Print a directory tree structure"""
        print(f"\n{cls._colorize('📁', 'CYAN')} {cls._colorize('Output Structure:', 'BOLD')}")
        print(f"{cls._colorize(str(base_path), 'CYAN')}")
        
        for i, (name, description) in enumerate(items):
            is_last = i == len(items) - 1
            prefix = "└── " if is_last else "├── "
            print(f"{prefix}{cls._colorize(name, 'WHITE')} - {cls._colorize(description, 'DIM')}")

# Global logger instance
log = Logger()

class QuestionGenerationPipeline:
    """3-step pipeline for generating high-leverage audience questions"""
    
    def __init__(self, client: OpenAIClient = None):
        self.client = client or OpenAIClient()
        self.config = CompletionConfig(model=ModelType.GPT_5_NANO)
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
        start_time = time.time()
        
        log.info(f"Processing chunk {chunk_number} ({len(chunk):,} chars)", indent=1)
        
        try:
            # Step 1: Summarization
            step1_start = time.time()
            log.info("Step 1: Summarization Layer", indent=2)
            summary = self.step1_summarization(chunk)
            
            main_points = len(summary.get('main_points', []))
            assumptions = len(summary.get('assumptions', []))
            log.success(f"Extracted {main_points} main points, {assumptions} assumptions", indent=3)
            
            # Step 2: Critical Thinking
            step2_start = time.time()
            log.info("Step 2: Critical Thinking Layer", indent=2)
            critical_analysis = self.step2_critical_thinking(summary)
            
            weak_spots = len(critical_analysis.get('weak_spots', []))
            contrarian = len(critical_analysis.get('contrarian_angles', []))
            log.success(f"Identified {weak_spots} weak spots, {contrarian} contrarian angles", indent=3)
            
            # Step 3: Question Generation
            step3_start = time.time()
            log.info("Step 3: Question Generation & Ranking", indent=2)
            questions = self.step3_question_generation(critical_analysis)
            
            question_count = len(questions.get('questions', []))
            if question_count > 0:
                top_question = max(questions.get('questions', []), key=lambda x: x.get('rank', 0))
                top_rank = top_question.get('rank', 0)
                log.success(f"Generated {question_count} questions (top rank: {top_rank})", indent=3)
            
            total_time = time.time() - start_time
            log.processing_time(start_time, f"Chunk {chunk_number}")
            
            return {
                'chunk_number': chunk_number,
                'original_text': chunk,
                'summary': summary,
                'critical_analysis': critical_analysis,
                'questions': questions,
                'char_count': len(chunk),
                'processing_time': total_time
            }
            
        except Exception as e:
            log.error(f"Chunk {chunk_number} failed: {str(e)}", indent=2)
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

def adaptive_chunking_strategy(text_length, content_type="transcript"):
    """Determine optimal chunking parameters based on content characteristics."""
    strategies = {
        "short": {"buffer": 2, "threshold": 85, "reason": "Dense content, smaller chunks"},
        "medium": {"buffer": 3, "threshold": 92, "reason": "Balanced approach"},
        "long": {"buffer": 4, "threshold": 95, "reason": "Longer content, larger chunks"},
        "technical": {"buffer": 5, "threshold": 88, "reason": "Technical content needs context"}
    }
    
    # Determine strategy based on length
    if text_length < 10000:
        strategy = "short"
    elif text_length < 50000:
        strategy = "medium"
    else:
        strategy = "long"
    
    return strategies[strategy]

def post_process_chunks(chunks):
    """Post-process chunks to ensure quality and consistency."""
    processed_chunks = []
    
    for i, chunk in enumerate(chunks):
        # Skip chunks that are too small
        if len(chunk) < MIN_CHUNK_SIZE:
            if i > 0:  # Merge with previous chunk
                processed_chunks[-1] += f"\n\n{chunk}"
                continue
            elif i < len(chunks) - 1:  # Merge with next chunk
                chunks[i + 1] = f"{chunk}\n\n{chunks[i + 1]}"
                continue
        
        # Split chunks that are too large
        if len(chunk) > MAX_CHUNK_SIZE:
            # Split at sentence boundaries
            sentences = chunk.split('. ')
            current_chunk = ""
            
            for sentence in sentences:
                if len(current_chunk + sentence) > MAX_CHUNK_SIZE and current_chunk:
                    processed_chunks.append(current_chunk.strip())
                    current_chunk = sentence + ". "
                else:
                    current_chunk += sentence + ". "
            
            if current_chunk.strip():
                processed_chunks.append(current_chunk.strip())
        else:
            processed_chunks.append(chunk)
    
    return processed_chunks

def experimental_chunking_strategies(text, strategy="hybrid"):
    """Try alternative chunking approaches for comparison."""
    from llama_index.core.node_parser import SentenceSplitter, TokenTextSplitter
    
    strategies = {}
    
    if strategy in ["hybrid", "all"]:
        # Hybrid: Sentence + semantic boundaries
        sentence_splitter = SentenceSplitter(
            chunk_size=1500,
            chunk_overlap=150,
            separator=" "
        )
        doc = Document(text=text)
        sentence_chunks = [node.get_content() for node in sentence_splitter.get_nodes_from_documents([doc])]
        strategies["sentence_based"] = sentence_chunks
    
    if strategy in ["token", "all"]:
        # Token-based chunking
        token_splitter = TokenTextSplitter(
            chunk_size=400,  # tokens
            chunk_overlap=50,
            separator=" "
        )
        doc = Document(text=text)
        token_chunks = [node.get_content() for node in token_splitter.get_nodes_from_documents([doc])]
        strategies["token_based"] = token_chunks
    
    return strategies

def add_chunk_overlap(chunks):
    """Add overlapping context between chunks for better continuity."""
    if not chunks or len(chunks) <= 1:
        return chunks
    
    overlapped_chunks = []
    
    for i, chunk in enumerate(chunks):
        enhanced_chunk = chunk
        
        # Add context from previous chunk
        if i > 0 and OVERLAP_SIZE > 0:
            prev_overlap = chunks[i-1][-OVERLAP_SIZE:].strip()
            if prev_overlap:
                enhanced_chunk = f"[Previous context: ...{prev_overlap}]\n\n{chunk}"
        
        overlapped_chunks.append(enhanced_chunk)
    
    return overlapped_chunks

def load_and_chunk_transcript(file_path, dirs):
    """Load transcript and perform enhanced semantic chunking with artifact saving."""
    try:
        # Load raw text
        with open(file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
        
        # Clean the text
        clean_text = clean_transcript_text(raw_text)
        
        # Save cleaned text artifacts
        cleaned_file, cleaning_stats = save_cleaned_text(dirs, raw_text, clean_text)
        log.file_saved(cleaned_file, "Cleaned transcript text")
        log.metric("Text reduction", f"{cleaning_stats['reduction_ratio']:.1%}", color='GREEN')
        log.metric("Original chars", f"{cleaning_stats['raw_char_count']:,}")
        log.metric("Cleaned chars", f"{cleaning_stats['cleaned_char_count']:,}")
        
        # Determine optimal chunking strategy
        strategy = adaptive_chunking_strategy(len(clean_text))
        log.info(f"Using {strategy['reason'].lower()}")
        log.metric("Buffer size", strategy['buffer'])
        log.metric("Threshold", f"{strategy['threshold']}%")
        
        # Create document
        doc = Document(text=clean_text)
        
        # Set up semantic chunking with adaptive parameters
        embed = OpenAIEmbedding()
        parser = SemanticSplitterNodeParser(
            embed_model=embed,
            buffer_size=strategy['buffer'],
            breakpoint_percentile_threshold=strategy['threshold']
        )
        
        # Generate semantic chunks
        log.info("Generating semantic chunks...")
        nodes = parser.get_nodes_from_documents([doc])
        raw_chunks = [n.get_content() for n in nodes]
        
        # Post-process chunks for quality
        log.info("Post-processing chunks...")
        processed_chunks = post_process_chunks(raw_chunks)
        
        # Add overlapping context
        if OVERLAP_SIZE > 0:
            log.info("Adding overlapping context...")
            final_chunks = add_chunk_overlap(processed_chunks)
        else:
            final_chunks = processed_chunks
        
        # Save chunk artifacts with enhanced metadata
        chunking_config = {
            'buffer_size': strategy['buffer'],
            'breakpoint_threshold': strategy['threshold'],
            'embedding_model': 'text-embedding-ada-002',
            'min_chunk_size': MIN_CHUNK_SIZE,
            'max_chunk_size': MAX_CHUNK_SIZE,
            'overlap_size': OVERLAP_SIZE,
            'strategy_used': strategy['reason'],
            'post_processing': True
        }
        
        chunk_files, chunk_index = save_chunks(dirs, final_chunks, chunking_config)
        log.success(f"Generated {len(final_chunks)} enhanced semantic chunks")
        log.file_saved(chunk_index, "Enhanced chunk index and metadata")
        
        # Show enhanced chunk statistics
        chunk_sizes = [len(chunk) for chunk in final_chunks]
        avg_size = sum(chunk_sizes) / len(chunk_sizes)
        min_size = min(chunk_sizes)
        max_size = max(chunk_sizes)
        
        log.metric("Average chunk size", f"{avg_size:.0f}", " chars")
        log.metric("Size range", f"{min_size:,} - {max_size:,}", " chars")
        log.metric("Size variance", f"{(max_size - min_size):,}", " chars")
        
        # Quality metrics
        optimal_chunks = sum(1 for size in chunk_sizes if MIN_CHUNK_SIZE <= size <= MAX_CHUNK_SIZE)
        quality_ratio = optimal_chunks / len(chunk_sizes)
        log.metric("Quality ratio", f"{quality_ratio:.1%}", color='GREEN' if quality_ratio > 0.8 else 'YELLOW')
        
        # Optional: Compare with alternative strategies for analysis
        if len(clean_text) > 5000:  # Only for larger texts
            log.info("Analyzing alternative chunking strategies...")
            alt_strategies = experimental_chunking_strategies(clean_text, "hybrid")
            
            for name, alt_chunks in alt_strategies.items():
                alt_sizes = [len(chunk) for chunk in alt_chunks]
                alt_avg = sum(alt_sizes) / len(alt_sizes) if alt_sizes else 0
                log.metric(f"{name} avg size", f"{alt_avg:.0f}", " chars", color='GRAY')
                log.metric(f"{name} count", len(alt_chunks), color='GRAY')
        
        return final_chunks, clean_text, cleaning_stats
        
    except FileNotFoundError:
        log.error(f"Transcript file not found: {file_path}")
        return None, None, None
    except Exception as e:
        log.error(f"Error processing transcript: {e}")
        return None, None, None

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
    chunks, clean_text, cleaning_stats = load_and_chunk_transcript(INPUT_TXT, dirs)
    
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