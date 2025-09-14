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
        Path("data/transcripts").mkdir(parents=True, exist_ok=True)
        Path("data/partials").mkdir(parents=True, exist_ok=True)
        Path("data/outputs").mkdir(parents=True, exist_ok=True)
        Path(self.partials_dir).mkdir(parents=True, exist_ok=True)
    
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
            # Temporarily change working directory context for analyze_chunks
            original_cwd = os.getcwd()
            
            # Set environment variables for the analysis script
            os.environ['TRANSCRIPT_PATH'] = self.transcript_path
            os.environ['PARTIALS_DIR'] = self.partials_dir
            
            # Import and run analysis
            from analyze_chunk import analyze_transcript
            success = analyze_transcript(self.transcript_path, self.partials_dir)
            
            if success:
                print(f"✓ Analysis completed successfully")
                return True
            else:
                print(f"✗ Analysis failed")
                return False
                
        except Exception as e:
            print(f"✗ Analysis failed: {e}")
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