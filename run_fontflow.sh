#!/bin/bash

# FontFlow Studio - Auto-Setup and Launcher
# For Linux and macOS

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Store starting directory
STARTDIR=$(pwd)

echo "      FontFlow Studio - Auto-Setup"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR] Python 3 is not installed!${NC}"
    echo ""
    echo "Please install Python 3.11+ from:"
    echo "  - Ubuntu/Debian: sudo apt install python3 python3-venv python3-pip"
    echo "  - Fedora: sudo dnf install python3 python3-virtualenv python3-pip"
    echo "  - macOS: brew install python3"
    echo "  - Or download from https://python.org"
    echo ""
    exit 1
fi

# Check Python version
PYVER=$(python3 --version 2>&1 | cut -d' ' -f2)
MAJOR=$(echo $PYVER | cut -d'.' -f1)
MINOR=$(echo $PYVER | cut -d'.' -f2)

if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 11 ]); then
    echo -e "${RED}[ERROR] Python 3.11+ is required. Detected: $PYVER${NC}"
    echo ""
    echo "Please upgrade Python to 3.11 or newer."
    exit 1
fi

echo -e "${GREEN}[OK] Python found: $PYVER${NC}"
echo ""

# Check if Git is installed (optional - for updates)
if command -v git &> /dev/null; then
    echo -e "${GREEN}[OK] Git found:$(git --version)${NC}"
    SKIP_GIT=0
    echo ""
else
    echo -e "${YELLOW}[WARN] Git not found - skipping auto-update${NC}"
    echo "If you want updates, install Git:"
    echo "  - Ubuntu/Debian: sudo apt install git"
    echo "  - Fedora: sudo dnf install git"
    echo "  - macOS: brew install git"
    echo ""
    SKIP_GIT=1
fi

# Check if we're in the FontFlow directory
if [ ! -f "main.py" ]; then
    echo -e "${RED}[ERROR] Cannot find main.py!${NC}"
    echo ""
    echo "Make sure you run this script from the FontFlow folder."
    echo "Current directory: $(pwd)"
    echo ""
    exit 1
fi

# Check for updates (if Git is available)
if [ $SKIP_GIT -eq 0 ]; then
    echo "[UPDATE] Checking for updates..."
    git fetch origin 2>/dev/null || true
    
    # Check if there are updates
    LOCAL=$(git rev-parse @ 2>/dev/null || echo "")
    REMOTE=$(git rev-parse @{u} 2>/dev/null || echo "")
    
    if [ -n "$LOCAL" ] && [ -n "$REMOTE" ] && [ "$LOCAL" != "$REMOTE" ]; then
        echo -e "${YELLOW}Updates available!${NC}"
        read -p "Pull latest changes? (y/n): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git pull origin main
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}[OK] Successfully updated to latest version${NC}"
            else
                echo -e "${YELLOW}[WARN] Git pull failed, continuing with existing files...${NC}"
            fi
        fi
    else
        echo "[OK] Already up to date"
    fi
    echo ""
fi

echo "[SETUP] Setting up Python virtual environment..."

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}[ERROR] Failed to create virtual environment!${NC}"
        exit 1
    fi
    echo -e "${GREEN}[OK] Virtual environment created${NC}"
else
    echo -e "${GREEN}[OK] Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR] Failed to activate virtual environment!${NC}"
    exit 1
fi

echo -e "${GREEN}[OK] Virtual environment activated${NC}"
echo ""

# Check for requirements.txt
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}[ERROR] requirements.txt not found!${NC}"
    echo "Please make sure you are in the correct directory."
    exit 1
fi

# Install/upgrade dependencies
echo "[INSTALL] Installing/updating dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo -e "${YELLOW}[ERROR] Failed to install some dependencies!${NC}"
    echo "Try installing manually: pip install -r requirements.txt"
    echo ""
else
    echo -e "${GREEN}[OK] All dependencies installed successfully${NC}"
fi

echo ""
echo "[LAUNCH] Starting FontFlow Studio..."
echo ""
echo "   Setup Complete! Starting App..."
echo ""

# Start the application
python main.py

echo ""
echo -e "${GREEN}[DONE] FontFlow Studio closed.${NC}"
echo "You can re-run this script anytime to update and launch the app."
echo ""

# Return to original directory
cd "$STARTDIR"