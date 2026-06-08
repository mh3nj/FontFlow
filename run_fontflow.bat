@echo off
title FontFlow Studio - Auto-Setup and Launcher
color 0A

setlocal enabledelayedexpansion

REM Store the starting directory
set STARTDIR=%CD%

echo       FontFlow Studio - Auto-Setup
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo.
    echo Please install Python 3.11+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

REM Check Python version (must be 3.11+)
for /f "tokens=2 delims= " %%v in ('python --version') do set PYVER=%%v
for /f "tokens=1,2 delims=." %%a in ("!PYVER!") do (
    set MAJOR=%%a
    set MINOR=%%b
)

if !MAJOR! LSS 3 (
    echo [ERROR] Python 3.11+ is required. Detected: !PYVER!
    pause
    exit /b 1
)
if !MAJOR! EQU 3 if !MINOR! LSS 11 (
    echo [ERROR] Python 3.11+ is required. Detected: !PYVER!
    pause
    exit /b 1
)

echo [OK] Python found: !PYVER!
echo.

REM Check if Git is installed (optional - for updates)
git --version >nul 2>&1
if errorlevel 1 (
    echo [WARN] Git not found - skipping auto-update
    echo.
    echo If you want updates, install Git from:
    echo https://git-scm.com/download/win
    echo.
    set SKIP_GIT=1
) else (
    echo [OK] Git found: 
    git --version
    echo.
    set SKIP_GIT=0
)

REM Create assets folders if they don't exist
if not exist "assets\icons" (
    mkdir assets\icons 2>nul
    mkdir assets\logo 2>nul
    echo [INFO] Created assets/icons and assets/logo folders
    echo.
)

REM Check if we're in the FontFlow directory
if not exist "main.py" (
    echo [ERROR] Cannot find main.py!
    echo.
    echo Make sure you run this script from the FontFlow folder.
    echo Current directory: %CD%
    echo.
    pause
    exit /b 1
)

REM Check for updates (if Git is available)
if !SKIP_GIT! EQU 0 (
    echo [UPDATE] Checking for updates...
    git fetch origin >nul 2>&1
    git status -uno >nul 2>&1
    echo.
    set /p UPDATE="Pull latest changes? (y/n): "
    if /i "!UPDATE!"=="y" (
        git pull origin main
        if errorlevel 1 (
            echo [WARN] Git pull failed, continuing with existing files...
        ) else (
            echo [OK] Successfully updated to latest version
        )
    )
    echo.
)

echo [SETUP] Setting up Python virtual environment...

REM Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment!
        cd /d "%STARTDIR%"
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment already exists
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment!
    cd /d "%STARTDIR%"
    pause
    exit /b 1
)

echo [OK] Virtual environment activated
echo.

REM Check for requirements.txt
if not exist "requirements.txt" (
    echo [ERROR] requirements.txt not found!
    echo Please make sure you are in the correct directory.
    cd /d "%STARTDIR%"
    pause
    exit /b 1
)

REM Install/upgrade dependencies
echo [INSTALL] Installing/updating dependencies...
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt

if errorlevel 1 (
    echo [ERROR] Failed to install some dependencies!
    echo.
    echo Try installing manually: pip install -r requirements.txt
    echo.
) else (
    echo [OK] All dependencies installed successfully
)

echo.
echo [LAUNCH] Starting FontFlow Studio...
echo.
echo    Setup Complete! Starting App...
echo.

REM Start the application
python main.py

echo.
echo [DONE] FontFlow Studio closed.
echo You can re-run this file anytime to update and launch the app.
echo.
echo Press any key to exit...
pause >nul

REM Return to original directory
cd /d "%STARTDIR%"
endlocal