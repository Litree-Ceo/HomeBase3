#!/usr/bin/env python3
"""
LiTree Social - Launcher Script
One-click startup for the social media platform.
"""

import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

def print_banner():
    print("""
==============================================================

         LiTree Social - Social Media Platform

              Powered by your AI Avatar Assistant

==============================================================
""")

def check_dependencies():
    """Check and install required packages."""
    print("[INFO] Checking dependencies...")
    
    required = ['flask', 'flask_cors', 'flask_socketio', 'flask_login', 'werkzeug']
    missing = []
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"   Installing missing packages: {', '.join(missing)}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("   [OK] Dependencies installed")
    else:
        print("   [OK] All dependencies present")

def setup_directories():
    """Create necessary directories."""
    print("[INFO] Setting up directories...")
    
    dirs = [
        'assets/avatars',
        'assets/videos',
        'assets/audio',
        'uploads/avatars',
        'uploads/posts',
        'uploads/media',
        'data'
    ]
    
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
    
    print("   [OK] Directories ready")

def check_env():
    """Check environment variables."""
    print("[INFO] Checking environment...")
    
    # Check for .env file
    if not Path('.env').exists() and Path('.env.example').exists():
        print("   [INFO] Creating .env file from template")
        import shutil
        shutil.copy('.env.example', '.env')

def launch_app():
    """Launch the social media app."""
    print("\n[START] Starting LiTree Social...\n")
    
    sys.path.insert(0, str(Path(__file__).parent))
    
    try:
        from app import app, socketio, init_db
        
        # Initialize database
        init_db()
        
        # Open browser after short delay
        def open_browser():
            time.sleep(2)
            webbrowser.open('http://localhost:5000')
        
        import threading
        threading.Thread(target=open_browser, daemon=True).start()
        
        print("[OK] Server running at: http://localhost:5000")
        print("[INFO] Open this URL on any device on your network")
        print("\n[INFO] Default login: create an account at /register")
        print("\n[FEATURES]")
        print("  - User Authentication (Free/Premium/VIP tiers)")
        print("  - Posts, Comments, Likes")
        print("  - Real-time Messaging")
        print("  - Friend System")
        print("  - Notifications")
        print("  - AI Avatar Assistant (LitBit)")
        print("  - Media Builder")
        print("\nPress Ctrl+C to stop\n")
        
        socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
        
    except ImportError as e:
        print(f"❌ Error importing app: {e}")
        print("   Run: pip install -r requirements.txt")
        sys.exit(1)

def main():
    print_banner()
    
    try:
        check_dependencies()
        setup_directories()
        check_env()
        launch_app()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
