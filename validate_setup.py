#!/usr/bin/env python3
"""
Setup validation script for Audio Brief Generator.
Validates all prerequisites before running the pipeline.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def validate_openai_api_key():
    """Validate OPENAI_API_KEY is present and properly formatted."""
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        return False, "OPENAI_API_KEY environment variable not set"
    
    if not api_key.startswith('sk-'):
        return False, "Invalid OPENAI_API_KEY format (should start with 'sk-')"
    
    if len(api_key) < 20:
        return False, "OPENAI_API_KEY appears to be too short"
    
    return True, "OpenAI API key validated"

def validate_dependencies():
    """Check if required Python packages are installed."""
    # Map package names to their import names
    required_packages = {
        'faster-whisper': 'faster_whisper',
        'openai': 'openai', 
        'pydub': 'pydub',
        'python-dotenv': 'dotenv'
    }
    
    missing_packages = []
    
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        return False, f"Missing packages: {', '.join(missing_packages)}"
    
    return True, "All required packages installed"

def validate_config_files():
    """Check if required configuration files exist."""
    required_files = [
        'config/per_chunk.md',
        'config/merge.md'
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        return False, f"Missing config files: {', '.join(missing_files)}"
    
    return True, "All config files found"

def validate_directories():
    """Check if required directories exist or can be created."""
    required_dirs = [
        'data/transcripts',
        'data/partials', 
        'data/outputs'
    ]
    
    for dir_path in required_dirs:
        try:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            return False, f"Cannot create directory {dir_path}: {e}"
    
    return True, "All directories validated"

def main():
    """Run all validation checks."""
    print("Audio Brief Generator - Setup Validation")
    print("=" * 50)
    
    checks = [
        ("OpenAI API Key", validate_openai_api_key),
        ("Python Dependencies", validate_dependencies),
        ("Configuration Files", validate_config_files),
        ("Output Directories", validate_directories)
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        try:
            passed, message = check_func()
            status = "✓" if passed else "✗"
            print(f"{status} {check_name}: {message}")
            
            if not passed:
                all_passed = False
                
        except Exception as e:
            print(f"✗ {check_name}: Error during validation - {e}")
            all_passed = False
    
    print("=" * 50)
    
    if all_passed:
        print("✓ All validation checks passed! Ready to run the pipeline.")
        sys.exit(0)
    else:
        print("✗ Some validation checks failed. Please fix the issues above.")
        print("\nTo fix missing packages, run: pip install -r requirements.txt")
        print("To fix missing config files, check the config/ directory")
        print("To fix API key issues, check your .env file")
        sys.exit(1)

if __name__ == "__main__":
    main()