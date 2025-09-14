#!/usr/bin/env python3
"""
Live audio recording module for capturing talks/presentations.
Records audio in real-time and saves to data/audio/ directory.
"""

import os
import sys
import time
import threading
from pathlib import Path
from datetime import datetime
import logging
import sounddevice as sd
import soundfile as sf
import numpy as np

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AudioRecorder:
    """Real-time audio recorder with live monitoring."""
    
    def __init__(self, output_dir="data/audio", sample_rate=44100, channels=1):
        self.output_dir = Path(output_dir)
        self.sample_rate = sample_rate
        self.channels = channels
        self.is_recording = False
        self.audio_data = []
        self.output_file = None
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Audio monitoring
        self.volume_threshold = 0.01  # Minimum volume to detect speech
        self.silence_duration = 0
        self.max_silence = 30  # Stop after 30 seconds of silence
        
    def list_audio_devices(self):
        """List available audio input devices."""
        print("Available audio input devices:")
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                print(f"  {i}: {device['name']} (channels: {device['max_input_channels']})")
        return devices
    
    def test_audio_input(self, device_id=None, duration=3):
        """Test audio input for a few seconds."""
        print(f"Testing audio input for {duration} seconds...")
        print("Speak into your microphone...")
        
        try:
            # Record test audio
            test_audio = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=self.channels,
                device=device_id,
                dtype='float64'
            )
            sd.wait()  # Wait for recording to complete
            
            # Analyze volume levels
            max_volume = np.max(np.abs(test_audio))
            avg_volume = np.mean(np.abs(test_audio))
            
            print(f"Audio test results:")
            print(f"  Max volume: {max_volume:.4f}")
            print(f"  Average volume: {avg_volume:.4f}")
            
            if max_volume < 0.001:
                print("⚠️  Very low audio levels detected. Check microphone connection.")
            elif max_volume < 0.01:
                print("⚠️  Low audio levels. Consider increasing microphone gain.")
            else:
                print("✓ Audio levels look good!")
                
            return max_volume > 0.001
            
        except Exception as e:
            print(f"✗ Audio test failed: {e}")
            return False
    
    def audio_callback(self, indata, frames, time, status):
        """Callback function for real-time audio processing."""
        if status:
            logging.warning(f"Audio callback status: {status}")
        
        if self.is_recording:
            # Add audio data to buffer
            self.audio_data.append(indata.copy())
            
            # Monitor volume for silence detection
            volume = np.sqrt(np.mean(indata**2))
            
            if volume < self.volume_threshold:
                self.silence_duration += frames / self.sample_rate
            else:
                self.silence_duration = 0
    
    def start_recording(self, filename=None, device_id=None, auto_stop=True):
        """Start recording audio."""
        if self.is_recording:
            print("Recording already in progress!")
            return False
        
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recording_{timestamp}.wav"
        
        # Ensure .wav extension
        if not filename.endswith('.wav'):
            filename += '.wav'
        
        self.output_file = self.output_dir / filename
        self.audio_data = []
        self.silence_duration = 0
        self.is_recording = True
        
        print(f"Starting recording: {self.output_file}")
        print("Press Ctrl+C to stop recording")
        
        try:
            # Start audio stream
            with sd.InputStream(
                callback=self.audio_callback,
                device=device_id,
                channels=self.channels,
                samplerate=self.sample_rate,
                dtype='float64'
            ):
                start_time = time.time()
                
                while self.is_recording:
                    time.sleep(0.1)  # Check every 100ms
                    
                    # Auto-stop on prolonged silence
                    if auto_stop and self.silence_duration > self.max_silence:
                        print(f"\nAuto-stopping after {self.max_silence}s of silence")
                        break
                    
                    # Show recording status
                    elapsed = time.time() - start_time
                    if int(elapsed) % 10 == 0 and elapsed > 0:  # Every 10 seconds
                        print(f"Recording... {elapsed:.0f}s (silence: {self.silence_duration:.1f}s)")
                        time.sleep(1)  # Prevent multiple prints
            
        except KeyboardInterrupt:
            print("\nRecording stopped by user")
        except Exception as e:
            print(f"Recording error: {e}")
            return False
        finally:
            self.is_recording = False
        
        # Save recorded audio
        return self.save_recording()
    
    def stop_recording(self):
        """Stop the current recording."""
        if self.is_recording:
            self.is_recording = False
            print("Stopping recording...")
            return True
        return False
    
    def save_recording(self):
        """Save the recorded audio data to file."""
        if not self.audio_data:
            print("No audio data to save!")
            return False
        
        try:
            # Concatenate all audio chunks
            audio_array = np.concatenate(self.audio_data, axis=0)
            
            # Save as WAV file
            sf.write(
                str(self.output_file),
                audio_array,
                self.sample_rate,
                format='WAV',
                subtype='PCM_16'
            )
            
            # Get file info
            duration = len(audio_array) / self.sample_rate
            file_size = self.output_file.stat().st_size
            
            print(f"✓ Recording saved: {self.output_file}")
            print(f"  Duration: {duration:.1f} seconds")
            print(f"  File size: {file_size / (1024*1024):.1f} MB")
            
            return str(self.output_file)
            
        except Exception as e:
            print(f"✗ Failed to save recording: {e}")
            return False

def interactive_recording():
    """Interactive recording session with device selection."""
    recorder = AudioRecorder()
    
    print("Audio Recording Setup")
    print("=" * 40)
    
    # List devices
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
    
    # Test audio
    print(f"\nTesting audio input...")
    if not recorder.test_audio_input(device_id):
        print("Audio test failed. Check your microphone setup.")
        return None
    
    # Recording settings
    filename = input("\nEnter filename (or press Enter for auto-generated): ").strip()
    if filename == "":
        filename = None
    
    auto_stop = input("Auto-stop on silence? (y/n, default: y): ").strip().lower()
    auto_stop = auto_stop != 'n'
    
    print(f"\nReady to record!")
    input("Press Enter to start recording...")
    
    # Start recording
    output_file = recorder.start_recording(filename, device_id, auto_stop)
    
    if output_file:
        print(f"\n✓ Recording complete: {output_file}")
        return output_file
    else:
        print("\n✗ Recording failed")
        return None

def main():
    """Main entry point for command line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Record audio for pipeline processing')
    parser.add_argument('--filename', '-f', help='Output filename')
    parser.add_argument('--device', '-d', type=int, help='Audio device ID')
    parser.add_argument('--list-devices', action='store_true', help='List audio devices')
    parser.add_argument('--test', action='store_true', help='Test audio input')
    parser.add_argument('--interactive', '-i', action='store_true', help='Interactive mode')
    parser.add_argument('--no-auto-stop', action='store_true', help='Disable auto-stop on silence')
    
    args = parser.parse_args()
    
    recorder = AudioRecorder()
    
    if args.list_devices:
        recorder.list_audio_devices()
        return
    
    if args.test:
        recorder.test_audio_input(args.device)
        return
    
    if args.interactive:
        output_file = interactive_recording()
    else:
        auto_stop = not args.no_auto_stop
        output_file = recorder.start_recording(args.filename, args.device, auto_stop)
    
    if output_file:
        print(f"\nRecording saved: {output_file}")
        
        # Ask if user wants to run the pipeline
        run_pipeline = input("\nRun pipeline on this recording? (y/n): ").strip().lower()
        if run_pipeline == 'y':
            print(f"\nTo process this recording, run:")
            print(f"python pipeline.py '{output_file}'")
    
    return output_file

if __name__ == "__main__":
    main()