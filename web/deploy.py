#!/usr/bin/env python3
"""
Deployment script for the Web Audio Recorder application.

This script helps with production deployment by checking requirements,
setting up the environment, and providing deployment guidance.
"""

import os
import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Check if Python version meets requirements."""
    if sys.version_info < (3, 7):
        print(f"❌ Python 3.7+ required, found {sys.version}")
        return False
    print(f"✅ Python version: {sys.version}")
    return True


def check_virtual_environment():
    """Check if running in a virtual environment."""
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    
    if in_venv:
        print(f"✅ Virtual environment: {sys.prefix}")
        return True
    else:
        print("⚠️  Not running in a virtual environment")
        print("   Consider using: python -m venv .venv && source .venv/bin/activate")
        return False


def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = [
        'flask',
        'flask-socketio',
        'werkzeug'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\nInstall missing packages with:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True


def check_environment_file():
    """Check if environment configuration exists."""
    env_file = Path('.env')
    env_example = Path('.env.example')
    
    if env_file.exists():
        print("✅ .env file found")
        return True
    elif env_example.exists():
        print("⚠️  .env file not found, but .env.example exists")
        print("   Copy .env.example to .env and configure as needed")
        return False
    else:
        print("❌ No environment configuration found")
        return False


def check_directories():
    """Check if required directories exist and are writable."""
    project_root = Path(__file__).parent.parent
    required_dirs = [
        project_root / 'data' / '1_audio',
        project_root / 'data' / 'outputs',
        Path(__file__).parent / 'static',
        Path(__file__).parent / 'logs'
    ]
    
    all_good = True
    
    for dir_path in required_dirs:
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            if os.access(dir_path, os.W_OK):
                print(f"✅ {dir_path}")
            else:
                print(f"❌ {dir_path} (not writable)")
                all_good = False
        except Exception as e:
            print(f"❌ {dir_path} ({e})")
            all_good = False
    
    return all_good


def check_static_files():
    """Check if required static files exist."""
    static_dir = Path(__file__).parent / 'static'
    required_files = [
        'index.html',
        'app.js',
        'style.css'
    ]
    
    all_good = True
    
    for filename in required_files:
        file_path = static_dir / filename
        if file_path.exists():
            print(f"✅ static/{filename}")
        else:
            print(f"❌ static/{filename}")
            all_good = False
    
    return all_good


def run_deployment_check():
    """Run all deployment checks."""
    print("🚀 Web Audio Recorder Deployment Check")
    print("=" * 50)
    
    checks = [
        ("Python Version", check_python_version),
        ("Virtual Environment", check_virtual_environment),
        ("Dependencies", check_dependencies),
        ("Environment Config", check_environment_file),
        ("Directories", check_directories),
        ("Static Files", check_static_files)
    ]
    
    results = []
    
    for check_name, check_func in checks:
        print(f"\n{check_name}:")
        result = check_func()
        results.append((check_name, result))
    
    print("\n" + "=" * 50)
    print("DEPLOYMENT CHECK SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{check_name:<20} {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 50)
    
    if all_passed:
        print("🎉 All checks passed! Ready for deployment.")
        print("\nTo start the application:")
        print("  python app.py")
        print("\nFor production deployment, consider:")
        print("  - Using a WSGI server like Gunicorn")
        print("  - Setting up a reverse proxy (nginx/Apache)")
        print("  - Configuring SSL/TLS certificates")
        print("  - Setting up process monitoring (systemd/supervisor)")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        return False
    
    return True


def create_systemd_service():
    """Create a systemd service file template."""
    service_content = f"""[Unit]
Description=Web Audio Recorder
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory={Path(__file__).parent.absolute()}
Environment=PATH={sys.executable}
Environment=FLASK_ENV=production
ExecStart={sys.executable} app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    service_file = Path('web-audio-recorder.service')
    service_file.write_text(service_content)
    print(f"✅ Created systemd service file: {service_file}")
    print("   To install: sudo cp web-audio-recorder.service /etc/systemd/system/")
    print("   To enable: sudo systemctl enable web-audio-recorder")
    print("   To start: sudo systemctl start web-audio-recorder")


def main():
    """Main deployment script."""
    if len(sys.argv) > 1:
        if sys.argv[1] == 'check':
            return run_deployment_check()
        elif sys.argv[1] == 'systemd':
            create_systemd_service()
            return True
        else:
            print("Usage: python deploy.py [check|systemd]")
            return False
    else:
        return run_deployment_check()


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)