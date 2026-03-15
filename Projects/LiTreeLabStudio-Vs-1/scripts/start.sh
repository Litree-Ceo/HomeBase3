#!/bin/bash

clear

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║           🤖 LiTree Avatar Assistant v2.0 🤖                 ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Check Python
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "❌ Python not found! Please install Python 3.8+"
    exit 1
fi

echo "✅ Python found"
echo ""

# Run launcher
python3 launch.py || python launch.py
