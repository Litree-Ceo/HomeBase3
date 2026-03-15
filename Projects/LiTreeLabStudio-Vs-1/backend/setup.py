#!/usr/bin/env python3
"""
LiTree Avatar Assistant - Setup Script
Quick setup and verification for the project.
"""

import os
import sys
import subprocess
from pathlib import Path

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def check_python_version():
    print("Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"[OK] Python {version.major}.{version.minor}.{version.micro} is supported!")
        return True
    else:
        print(f"[ERROR] Python {version.major}.{version.minor} is too old. Need 3.8+")
        return False

def install_dependencies():
    print("\nInstalling Python dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("[OK] Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to install dependencies: {e}")
        return False

def check_assets():
    print("\nChecking avatar assets...")
    assets_dir = Path("assets/avatars")
    
    if not assets_dir.exists():
        print("[!] Assets folder not found. Creating...")
        assets_dir.mkdir(parents=True, exist_ok=True)
    
    # Check for avatar images
    styles = ['pixar', 'cyberpunk', 'steampunk', 'anime']
    moods = ['happy', 'thinking', 'surprised', 'talking']
    
    found_count = 0
    expected_count = len(styles) * len(moods)
    
    for style in styles:
        for mood in moods:
            img_path = assets_dir / f"avatar_{style}_{mood}.png"
            if img_path.exists():
                found_count += 1
    
    if found_count == 0:
        print("[INFO] No custom avatar images found. Using emoji placeholders.")
        print("   Add your images to assets/avatars/ to customize!")
    else:
        print(f"[OK] Found {found_count}/{expected_count} avatar images")
    
    return True

def check_env():
    print("\nChecking environment...")
    api_key = os.getenv('OPENAI_API_KEY')
    
    if api_key:
        print("[OK] OPENAI_API_KEY is set (AI backend enabled)")
    else:
        print("[INFO] OPENAI_API_KEY not set")
        print("   Export it to enable AI responses, or use mock mode:")
        print("   export OPENAI_API_KEY='your-api-key-here'")
    
    return True

def create_env_file():
    env_file = Path(".env")
    if not env_file.exists():
        print("\nCreating .env template...")
        with open(env_file, 'w') as f:
            f.write("# OpenAI API Key (optional)\n")
            f.write("# Get yours at: https://platform.openai.com/api-keys\n")
            f.write("OPENAI_API_KEY=\n\n")
            f.write("# Flask settings\n")
            f.write("FLASK_DEBUG=true\n")
            f.write("FLASK_PORT=5000\n")
        print("[OK] Created .env template")

def print_next_steps():
    print_header("Setup Complete!")
    print("""
NEXT STEPS:

1. START SIMPLE (No backend):
   Open assistant.html in your browser
   
   OR use VS Code:
   - Press Ctrl+Shift+P
   - Type "Tasks: Run Task"
   - Select "Open Assistant in Browser"

2. START WITH BACKEND (AI powered):
   python backend.py
   Then open assistant.html in browser
   Enable "AI Backend" toggle in settings

3. CUSTOMIZE YOUR AVATAR:
   See ASSETS_GUIDE.md for instructions on adding your own images!

DOCUMENTATION:
   - README.md - Project overview
   - ASSETS_GUIDE.md - Creating avatar images
   - backend.py - API documentation

Happy chatting with your avatar!
""")

def main():
    print_header("LiTree Avatar Assistant - Setup")
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", install_dependencies),
        ("Assets", check_assets),
        ("Environment", check_env),
    ]
    
    all_passed = True
    for name, check_fn in checks:
        try:
            if not check_fn():
                all_passed = False
        except Exception as e:
            print(f"[ERROR] {name} check failed: {e}")
            all_passed = False
    
    create_env_file()
    
    if all_passed:
        print_next_steps()
        return 0
    else:
        print("\n[!] Some checks failed. See above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
