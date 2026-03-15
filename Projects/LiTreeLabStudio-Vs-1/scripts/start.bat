@echo off
chcp 65001 >nul
title LiTree Avatar Assistant
cls

echo ╔══════════════════════════════════════════════════════════════╗
echo ║                                                              ║
echo ║           🤖 LiTree Avatar Assistant v2.0 🤖                 ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

echo ✅ Python found
echo.

:: Run launcher
python launch.py

pause
