#!/usr/bin/env python3
"""
Record audio during a talk and automatically process it through the pipeline.
This is the main entry point for live recording + processing workflow.
"""

import sys
import os
from pathlib import Path
import argparse
from datetime import datetime

# Ensure we can import from the same directory
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from record_audio import AudioRecorder, interactive_recording
from pipeline import AudioBriefPipeline

def record_and_process(filename=None, device_id=None, auto_stop=True, output_name=None):
    """Record audio and immediately process through the pipeline."""
    
    print("🎙️  Audio Recording + Brief Generation")
    print("=" * 50)
    
    # Step 1: Record audio
    print("\n📹 STEP 1: RECORDING AUDIO")
    print("-" * 30)
    
    recorder = AudioRecorder()
    
    # Test audio first
    print("Testing audio input...")
    if not recorder.test_audio_input(device_id, duration=2):
        print("❌ Audio test failed. Please check your microphone.")
        return False
    
    print("✅ Audio test passed!")
    
    # Start recording
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"talk_{timestamp}.wav"
    
    print(f"\nStarting recording: {filename}")
    print("🔴 Recording... Press Ctrl+C to stop")
    
    audio_file = recorder.start_recording(filename, device_id, auto_stop)
    
    if not audio_file:
        print("❌ Recording failed!")
        return False
    
    print(f"✅ Recording completed: {audio_file}")
    
    # Step 2: Process through pipeline
    print(f"\n🔄 STEP 2: PROCESSING THROUGH PIPELINE")
    print("-" * 40)
    
    try:
        # Create and run pipeline
        pipeline = AudioBriefPipeline(audio_file, output_name)
        success = pipeline.run_full_pipeline()
        
        if success:
            print(f"\n🎉 SUCCESS!")
            print(f"📄 Brief generated: {pipeline.output_path}")
            print(f"🎵 Original recording: {audio_file}")
            return True
        else:
            print(f"\n❌ Pipeline processing failed")
            print(f"🎵 Recording saved: {audio_file}")
            return False
            
    except Exception as e:
        print(f"\n❌ Pipeline error: {e}")
        print(f"🎵 Recording saved: {audio_file}")
        return False

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Record audio during a talk and generate a brief',
        epilog='This tool records live audio and processes it through the full pipeline'
    )
    parser.add_argument('--filename', '-f', help='Recording filename (auto-generated if not provided)')
    parser.add_argument('--device', '-d', type=int, help='Audio device ID')
    parser.add_argument('--output-name', '-o', help='Output name for brief (defaults to recording name)')
    parser.add_argument('--no-auto-stop', action='store_true', help='Disable auto-stop on silence')
    parser.add_argument('--interactive', '-i', action='store_true', help='Interactive device selection')
    parser.add_argument('--list-devices', action='store_true', help='List available audio devices')
    parser.add_argument('--test-only', action='store_true', help='Only test audio, don\'t record')
    
    args = parser.parse_args()
    
    # Handle special modes
    if args.list_devices:
        recorder = AudioRecorder()
        recorder.list_audio_devices()
        return
    
    if args.test_only:
        recorder = AudioRecorder()
        success = recorder.test_audio_input(args.device, duration=5)
        print("✅ Audio test passed!" if success else "❌ Audio test failed!")
        return
    
    if args.interactive:
        # Interactive mode with device selection
        print("🎙️  Interactive Recording Mode")
        print("=" * 40)
        
        recorder = AudioRecorder()
        devices = recorder.list_audio_devices()
        
        # Device selection
        device_id = None
        while True:
            try:
                device_input = input("\nSelect device ID (or press Enter for default): ").strip()
                if device_input == "":
                    break
                device_id = int(device_input)
                if device_id < 0 or device_id >= len(devices):
                    print("Invalid device ID")
                    continue
                break
            except ValueError:
                print("Please enter a valid number")
        
        # Get filename
        filename = input("Enter recording filename (or press Enter for auto): ").strip()
        if filename == "":
            filename = None
        
        # Get output name
        output_name = input("Enter brief output name (or press Enter for auto): ").strip()
        if output_name == "":
            output_name = None
        
        # Auto-stop setting
        auto_stop_input = input("Auto-stop on silence? (y/n, default: y): ").strip().lower()
        auto_stop = auto_stop_input != 'n'
        
        success = record_and_process(filename, device_id, auto_stop, output_name)
    else:
        # Command line mode
        auto_stop = not args.no_auto_stop
        success = record_and_process(args.filename, args.device, auto_stop, args.output_name)
    
    if success:
        print("\n🎉 All done! Your brief is ready.")
    else:
        print("\n❌ Process completed with errors.")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()