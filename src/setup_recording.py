#!/usr/bin/env python3
"""
Setup script for audio recording dependencies.
Installs required packages and tests audio setup.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Command: {command}")
        print(f"   Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required, found {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def setup_virtual_environment():
    """Set up and activate virtual environment."""
    venv_path = Path(".venv")
    
    if not venv_path.exists():
        print("🔄 Creating virtual environment...")
        if not run_command("python3 -m venv .venv", "Virtual environment creation"):
            return False
    else:
        print("✅ Virtual environment already exists")
    
    # Check if we're in the virtual environment
    if sys.prefix == sys.base_prefix:
        print("⚠️  Not in virtual environment. Please run:")
        print("   source .venv/bin/activate  # On macOS/Linux")
        print("   .venv\\Scripts\\activate     # On Windows")
        print("   Then run this script again.")
        return False
    else:
        print("✅ Virtual environment is active")
        return True

def install_dependencies():
    """Install required Python packages."""
    print("🔄 Installing Python dependencies...")
    
    # Upgrade pip first
    if not run_command("pip install --upgrade pip", "Pip upgrade"):
        return False
    
    # Install requirements
    if not run_command("pip install -r requirements.txt", "Requirements installation"):
        return False
    
    return True

def test_audio_setup():
    """Test audio recording setup."""
    print("🔄 Testing audio setup...")
    
    try:
        # Add current directory to path for imports
        current_dir = Path(__file__).parent
        sys.path.insert(0, str(current_dir))
        from record_audio import AudioRecorder
        
        recorder = AudioRecorder()
        
        # List devices
        print("\n📱 Available audio devices:")
        devices = recorder.list_audio_devices()
        
        # Test default device
        print("\n🎤 Testing default microphone (speak for 3 seconds)...")
        success = recorder.test_audio_input(duration=3)
        
        if success:
            print("✅ Audio recording test passed!")
            return True
        else:
            print("❌ Audio recording test failed!")
            print("   Check your microphone connection and permissions.")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Some dependencies may not be installed correctly.")
        return False
    except Exception as e:
        print(f"❌ Audio test error: {e}")
        return False

def check_env_file():
    """Check if .env file exists with OpenAI API key."""
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  .env file not found")
        print("   Create .env file with your OpenAI API key:")
        print("   OPENAI_API_KEY=your_api_key_here")
        return False
    
    # Check if it contains OPENAI_API_KEY
    try:
        with open(env_file, 'r') as f:
            content = f.read()
            if "OPENAI_API_KEY" in content:
                print("✅ .env file found with OpenAI API key")
                return True
            else:
                print("⚠️  .env file exists but no OPENAI_API_KEY found")
                return False
    except Exception as e:
        print(f"❌ Error reading .env file: {e}")
        return False

def main():
    """Main setup process."""
    print("🎙️  Audio Recording Setup")
    print("=" * 40)
    
    success = True
    
    # Check Python version
    if not check_python_version():
        success = False
    
    # Check virtual environment
    if not setup_virtual_environment():
        success = False
    
    # Install dependencies
    if success and not install_dependencies():
        success = False
    
    # Check .env file
    if not check_env_file():
        success = False
    
    # Test audio setup
    if success and not test_audio_setup():
        success = False
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 Setup completed successfully!")
        print("\nYou can now use:")
        print("  python record_and_process.py --interactive")
        print("  python src/record_audio.py --interactive")
        print("  python pipeline.py <audio_file>")
    else:
        print("❌ Setup completed with errors")
        print("Please fix the issues above and run setup again.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)