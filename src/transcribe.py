#!/usr/bin/env python3
"""
Audio transcription script using faster-whisper.
Converts audio files to timestamped transcripts.
"""

import sys
import os
from pathlib import Path
from faster_whisper import WhisperModel
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def validate_audio_file(audio_path):
    """
    Comprehensive validation of audio file.
    
    Args:
        audio_path (str): Path to input audio file
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is unsupported or file is corrupted
        PermissionError: If file cannot be read
    """
    # Check if file exists
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    
    # Check if file is readable
    if not os.access(audio_path, os.R_OK):
        raise PermissionError(f"Cannot read audio file: {audio_path}")
    
    # Check file size (minimum 1KB, maximum 2GB)
    file_size = os.path.getsize(audio_path)
    if file_size < 1024:  # 1KB
        raise ValueError(f"Audio file too small (< 1KB): {audio_path}")
    if file_size > 2 * 1024 * 1024 * 1024:  # 2GB
        raise ValueError(f"Audio file too large (> 2GB): {audio_path}")
    
    # Validate audio format
    supported_formats = {'.wav', '.mp3', '.m4a', '.mp4', '.flac', '.ogg', '.webm', '.aac'}
    file_ext = Path(audio_path).suffix.lower()
    if file_ext not in supported_formats:
        raise ValueError(f"Unsupported audio format: {file_ext}. Supported formats: {', '.join(sorted(supported_formats))}")
    
    logging.info(f"Audio file validation passed: {audio_path} ({file_size / (1024*1024):.1f} MB)")

def transcribe_audio(audio_path, output_path="transcript.txt"):
    """
    Transcribe audio file using faster-whisper large-v3 model.
    
    Args:
        audio_path (str): Path to input audio file
        output_path (str): Path to output transcript file
        
    Returns:
        str: Path to generated transcript file
        
    Raises:
        FileNotFoundError: If audio file doesn't exist
        ValueError: If audio format is unsupported
        RuntimeError: If transcription fails
    """
    try:
        # Comprehensive audio file validation
        validate_audio_file(audio_path)
        
        # Create output directory if it doesn't exist
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logging.info(f"Loading faster-whisper base model...")
        # Initialize model with error handling
        try:
            model = WhisperModel("base", device="auto", compute_type="auto")
        except Exception as e:
            logging.error(f"Failed to load Whisper model: {e}")
            raise RuntimeError(f"Could not initialize Whisper model: {e}")
        
        logging.info(f"Starting transcription: {audio_path}")
        
        # Transcribe with word-level timestamps and error handling
        try:
            segments, info = model.transcribe(
                audio_path,
                beam_size=5,
                word_timestamps=True,
                language="en",  # Can be auto-detected if needed
                vad_filter=True,  # Voice activity detection to improve accuracy
                vad_parameters=dict(min_silence_duration_ms=500)
            )
        except Exception as e:
            logging.error(f"Transcription failed: {e}")
            raise RuntimeError(f"Audio transcription failed: {e}")
        
        logging.info(f"Detected language: {info.language} (probability: {info.language_probability:.2f})")
        logging.info(f"Audio duration: {info.duration:.2f} seconds")
        
        # Write timestamped transcript with error handling
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"# Transcript\n")
                f.write(f"Audio: {audio_path}\n")
                f.write(f"Language: {info.language} (confidence: {info.language_probability:.2f})\n")
                f.write(f"Duration: {info.duration:.2f}s\n\n")
                
                segment_count = 0
                for segment in segments:
                    # Write segment with timestamp
                    start_time = format_timestamp(segment.start)
                    end_time = format_timestamp(segment.end)
                    f.write(f"[{start_time} -> {end_time}] {segment.text.strip()}\n")
                    
                    # Write word-level timestamps if available
                    if hasattr(segment, 'words') and segment.words:
                        for word in segment.words:
                            word_start = format_timestamp(word.start)
                            word_end = format_timestamp(word.end)
                            f.write(f"  {word_start}-{word_end}: {word.word}\n")
                        f.write("\n")
                    
                    segment_count += 1
                
                logging.info(f"Processed {segment_count} segments")
                
        except IOError as e:
            logging.error(f"Failed to write transcript: {e}")
            raise RuntimeError(f"Could not write transcript to {output_path}: {e}")
        
        logging.info(f"Transcript saved successfully: {output_path}")
        return output_path
        
    except Exception as e:
        logging.error(f"Transcription process failed: {e}")
        raise

def format_timestamp(seconds):
    """Convert seconds to MM:SS format."""
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"

def main():
    """Main entry point for command line usage."""
    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else "data/transcripts/transcript.txt"
    else:
        print("Usage: python transcribe.py <audio_file> [output_file]")
        print("Supported formats: wav, mp3, m4a, mp4, flac, ogg, webm, aac")
        sys.exit(1)
    
    try:
        transcribe_audio(audio_file, output_file)
        print("✓ Transcription completed successfully!")
    except FileNotFoundError as e:
        print(f"✗ File Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"✗ Format Error: {e}")
        sys.exit(1)
    except PermissionError as e:
        print(f"✗ Permission Error: {e}")
        sys.exit(1)
    except RuntimeError as e:
        print(f"✗ Runtime Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected Error: {e}")
        logging.exception("Unexpected error during transcription")
        sys.exit(1)

if __name__ == "__main__":
    main()