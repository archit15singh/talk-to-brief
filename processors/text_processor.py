#!/usr/bin/env python3
"""
Text processing and transformation utilities
"""

import re
from llama_index.core import Document
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser import SemanticSplitterNodeParser, SentenceSplitter, TokenTextSplitter
from utils.logger import Logger

# Global logger instance
log = Logger()

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

def post_process_chunks(chunks, min_chunk_size=500, max_chunk_size=3000):
    """Post-process chunks to ensure quality and consistency."""
    processed_chunks = []
    
    for i, chunk in enumerate(chunks):
        # Skip chunks that are too small
        if len(chunk) < min_chunk_size:
            if i > 0:  # Merge with previous chunk
                processed_chunks[-1] += f"\n\n{chunk}"
                continue
            elif i < len(chunks) - 1:  # Merge with next chunk
                chunks[i + 1] = f"{chunk}\n\n{chunks[i + 1]}"
                continue
        
        # Split chunks that are too large
        if len(chunk) > max_chunk_size:
            # Split at sentence boundaries
            sentences = chunk.split('. ')
            current_chunk = ""
            
            for sentence in sentences:
                if len(current_chunk + sentence) > max_chunk_size and current_chunk:
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

def add_chunk_overlap(chunks, overlap_size=100):
    """Add overlapping context between chunks for better continuity."""
    if not chunks or len(chunks) <= 1:
        return chunks
    
    overlapped_chunks = []
    
    for i, chunk in enumerate(chunks):
        enhanced_chunk = chunk
        
        # Add context from previous chunk
        if i > 0 and overlap_size > 0:
            prev_overlap = chunks[i-1][-overlap_size:].strip()
            if prev_overlap:
                enhanced_chunk = f"[Previous context: ...{prev_overlap}]\n\n{chunk}"
        
        overlapped_chunks.append(enhanced_chunk)
    
    return overlapped_chunks

def load_and_chunk_transcript(file_path, dirs, buffer_size=3, breakpoint_threshold=92, min_chunk_size=500, max_chunk_size=3000, overlap_size=100):
    """Load transcript and perform enhanced semantic chunking with artifact saving."""
    from data.file_manager import save_cleaned_text, save_chunks
    
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
        embed = OpenAIEmbedding(model="text-embedding-3-small")
        parser = SemanticSplitterNodeParser(
            embed_model=embed,
            buffer_size=strategy['buffer'],
            breakpoint_percentile_threshold=strategy['threshold']
        )
        
        # Generate semantic chunks
        log.info("Generating semantic chunks...")
        nodes = parser.get_nodes_from_documents([doc])
        semantic_chunks = [node.get_content() for node in nodes]
        
        log.success(f"Generated {len(semantic_chunks)} semantic chunks")
        
        # Post-process chunks for quality
        log.info("Post-processing chunks for quality...")
        processed_chunks = post_process_chunks(semantic_chunks, min_chunk_size, max_chunk_size)
        
        # Add overlap for continuity
        log.info("Adding overlap for continuity...")
        final_chunks = add_chunk_overlap(processed_chunks, overlap_size)
        
        # Save chunking configuration
        chunking_config = {
            'buffer_size': strategy['buffer'],
            'breakpoint_threshold': strategy['threshold'],
            'min_chunk_size': min_chunk_size,
            'max_chunk_size': max_chunk_size,
            'overlap_size': overlap_size,
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
        optimal_chunks = sum(1 for size in chunk_sizes if min_chunk_size <= size <= max_chunk_size)
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