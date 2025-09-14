#!/usr/bin/env python3
"""
Audio Brief Generator Pipeline
Main orchestrator for the complete audio-to-brief generation process.
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Add src to path for imports
sys.path.insert(0, 'src')

from transcribe import transcribe_audio, validate_audio_file
from analyze_chunk import validate_openai_api_key
from merge_brief import merge_partials_to_brief

class AudioBriefPipeline:
    """Main pipeline orchestrator for audio brief generation."""
    
    def __init__(self, audio_file: str, output_name: str = None):
        self.audio_file = audio_file
        self.audio_path = Path(audio_file)
        
        # Validate audio file early
        validate_audio_file(audio_file)
        
        # Generate output name from audio file if not provided
        if output_name is None:
            self.output_name = self.audio_path.stem
        else:
            self.output_name = output_name
        
        # Set up paths
        self.transcript_path = f"data/transcripts/{self.output_name}_transcript.txt"
        self.partials_dir = f"data/partials/{self.output_name}"
        self.output_path = f"data/outputs/{self.output_name}_brief.md"
        
        # Create directories
        try:
            Path("data/transcripts").mkdir(parents=True, exist_ok=True)
            Path("data/partials").mkdir(parents=True, exist_ok=True)
            Path("data/outputs").mkdir(parents=True, exist_ok=True)
            Path(self.partials_dir).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise RuntimeError(f"Failed to create output directories: {e}")
    
    def validate_prerequisites(self):
        """Validate all prerequisites before starting the pipeline."""
        print("Validating prerequisites...")
        
        # Validate audio file
        validate_audio_file(self.audio_file)
        print("✓ Audio file validated")
        
        # Validate OpenAI API key
        validate_openai_api_key()
        print("✓ OpenAI API key validated")
        
        # Check required config files
        config_files = ["config/per_chunk.md", "config/merge.md"]
        for config_file in config_files:
            if not Path(config_file).exists():
                raise FileNotFoundError(f"Required config file missing: {config_file}")
        print("✓ Configuration files found")
        
        print("All prerequisites validated successfully!")
    
    def run_transcription(self) -> bool:
        """Step 1: Transcribe audio to text with timestamps."""
        print(f"\n{'='*60}")
        print(f"STEP 1: TRANSCRIPTION")
        print(f"{'='*60}")
        print(f"Audio file: {self.audio_file}")
        print(f"Output: {self.transcript_path}")
        
        try:
            transcribe_audio(self.audio_file, self.transcript_path)
            print(f"✓ Transcription completed successfully")
            return True
        except Exception as e:
            print(f"✗ Transcription failed: {e}")
            return False
    
    def run_analysis(self) -> bool:
        """Step 2: Analyze transcript chunks with GPT-4."""
        print(f"\n{'='*60}")
        print(f"STEP 2: CHUNK ANALYSIS")
        print(f"{'='*60}")
        print(f"Transcript: {self.transcript_path}")
        print(f"Partials output: {self.partials_dir}/")
        
        try:
            # Validate transcript exists
            if not Path(self.transcript_path).exists():
                raise FileNotFoundError(f"Transcript file not found: {self.transcript_path}")
            
            # Import and run analysis functions directly
            from analyze_chunk import (
                load_transcript, extract_segments_from_transcript, 
                create_intelligent_chunks, load_analysis_prompt,
                process_chunks_parallel, save_partials
            )
            
            # Load and process transcript
            transcript_content = load_transcript(self.transcript_path)
            segments = extract_segments_from_transcript(transcript_content)
            
            if not segments:
                raise ValueError("No timestamped segments found in transcript")
            
            chunks = create_intelligent_chunks(segments, target_words=1200)
            
            if not chunks:
                raise ValueError("No chunks created from transcript")
            
            print(f"Created {len(chunks)} chunks for analysis")
            
            # Load prompt and process chunks
            prompt = load_analysis_prompt()
            results = process_chunks_parallel(chunks, prompt, max_workers=4)
            save_partials(results, self.partials_dir)
            
            # Check success rate
            successful = sum(1 for r in results if r['success'])
            total = len(results)
            
            if successful == 0:
                print(f"✗ All chunks failed to process")
                return False
            elif successful < total:
                print(f"⚠️  Partial success: {successful}/{total} chunks processed")
                print("Continuing with available results...")
            else:
                print(f"✓ All {total} chunks processed successfully")
            
            return True
                
        except Exception as e:
            print(f"✗ Analysis failed: {e}")
            logging.exception("Analysis step failed")
            return False
    
    def run_merge(self) -> bool:
        """Step 3: Merge partial analyses into final brief."""
        print(f"\n{'='*60}")
        print(f"STEP 3: BRIEF GENERATION")
        print(f"{'='*60}")
        print(f"Partials: {self.partials_dir}/")
        print(f"Output: {self.output_path}")
        
        try:
            # Import and run merge
            from merge_brief import merge_partials_to_brief
            success = merge_partials_to_brief(self.partials_dir, self.output_path)
            
            if success:
                print(f"✓ Brief generation completed successfully")
                return True
            else:
                print(f"✗ Brief generation failed")
                return False
                
        except Exception as e:
            print(f"✗ Brief generation failed: {e}")
            return False
    
    def run_full_pipeline(self) -> bool:
        """Run the complete pipeline from audio to brief."""
        print(f"Audio Brief Generator Pipeline")
        print(f"Audio: {self.audio_file}")
        print(f"Output: {self.output_path}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Step 1: Transcription
        if not self.run_transcription():
            return False
        
        # Step 2: Analysis
        if not self.run_analysis():
            return False
        
        # Step 3: Merge
        if not self.run_merge():
            return False
        
        print(f"\n{'='*60}")
        print(f"PIPELINE COMPLETED SUCCESSFULLY")
        print(f"{'='*60}")
        print(f"Final brief: {self.output_path}")
        print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True

def main():
    """Main entry point for the pipeline."""
    parser = argparse.ArgumentParser(description='Generate brief from audio file')
    parser.add_argument('audio_file', help='Path to audio file')
    parser.add_argument('--output-name', '-o', help='Output name (defaults to audio filename)')
    parser.add_argument('--step', choices=['transcribe', 'analyze', 'merge'], 
                       help='Run only specific step')
    
    args = parser.parse_args()
    
    # Validate audio file exists
    if not os.path.exists(args.audio_file):
        print(f"Error: Audio file not found: {args.audio_file}")
        sys.exit(1)
    
    # Create pipeline
    pipeline = AudioBriefPipeline(args.audio_file, args.output_name)
    
    try:
        if args.step == 'transcribe':
            success = pipeline.run_transcription()
        elif args.step == 'analyze':
            success = pipeline.run_analysis()
        elif args.step == 'merge':
            success = pipeline.run_merge()
        else:
            success = pipeline.run_full_pipeline()
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\nPipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()