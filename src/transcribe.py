#!/usr/bin/env python3
"""
Audio transcription script using faster-whisper.
Converts audio files to timestamped transcripts.
"""

import sys
import os
from pathlib import Path
from faster_whisper import WhisperModel

def transcribe_audio(audio_path, output_path="transcript.txt"):
    """
    Transcribe audio file using faster-whisper large-v3 model.
    
    Args:
        audio_path (str): Path to input audio file
        output_path (str): Path to output transcript file
    """
    # Validate input file exists
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    
    # Validate audio format
    supported_formats = {'.wav', '.mp3', '.m4a', '.mp4', '.flac', '.ogg'}
    file_ext = Path(audio_path).suffix.lower()
    if file_ext not in supported_formats:
        raise ValueError(f"Unsupported audio format: {file_ext}. Supported: {', '.join(supported_formats)}")
    
    print(f"Loading faster-whisper large-v3 model...")
    # Initialize model with large-v3 for accuracy
    model = WhisperModel("large-v3", device="auto", compute_type="auto")
    
    print(f"Transcribing audio: {audio_path}")
    # Transcribe with word-level timestamps
    segments, info = model.transcribe(
        audio_path,
        beam_size=5,
        word_timestamps=True,
        language="en"  # Can be auto-detected if needed
    )
    
    print(f"Detected language: {info.language} (probability: {info.language_probability:.2f})")
    
    # Write timestamped transcript
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# Transcript\n")
        f.write(f"Audio: {audio_path}\n")
        f.write(f"Language: {info.language} (confidence: {info.language_probability:.2f})\n")
        f.write(f"Duration: {info.duration:.2f}s\n\n")
        
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
    
    print(f"Transcript saved to: {output_path}")
    return output_path

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
        sys.exit(1)
    
    try:
        transcribe_audio(audio_file, output_file)
        print("Transcription completed successfully!")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()