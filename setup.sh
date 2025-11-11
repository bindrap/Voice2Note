#!/bin/bash

# Voice2Note Setup Script
# This script automates the installation and setup process

set -e  # Exit on error

echo "================================================"
echo "Voice2Note Setup Script"
echo "================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running on Windows (WSL)
if grep -qi microsoft /proc/version 2>/dev/null; then
    echo -e "${YELLOW}Detected WSL environment${NC}"
    IS_WSL=true
else
    IS_WSL=false
fi

# Function to print success message
success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print error message
error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to print info message
info() {
    echo -e "${YELLOW}→ $1${NC}"
}

# Check Python version
info "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    success "Python $PYTHON_VERSION found"
else
    error "Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi

# Check FFmpeg
info "Checking FFmpeg..."
if command -v ffmpeg &> /dev/null; then
    success "FFmpeg found"
else
    error "FFmpeg not found. Please install FFmpeg:"
    echo "  Ubuntu/Debian: sudo apt install ffmpeg"
    echo "  macOS: brew install ffmpeg"
    exit 1
fi

# Create virtual environment
info "Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    success "Virtual environment created"
else
    success "Virtual environment already exists"
fi

# Activate virtual environment
info "Activating virtual environment..."
source venv/bin/activate
success "Virtual environment activated"

# Install Python dependencies
info "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
success "Python dependencies installed"

# Check if whisper.cpp exists
info "Checking for whisper.cpp..."
if [ ! -d "whisper.cpp" ]; then
    info "whisper.cpp not found. Cloning repository..."
    git clone https://github.com/ggml-org/whisper.cpp.git
    success "whisper.cpp cloned"

    info "Building whisper.cpp..."
    cd whisper.cpp
    cmake -B build
    cmake --build build -j --config Release
    cd ..
    success "whisper.cpp built successfully"
else
    success "whisper.cpp already exists"
fi

# Check for Whisper model
info "Checking for Whisper model..."
if [ ! -f "models/ggml-medium.bin" ]; then
    info "Downloading Whisper medium model (this may take a while)..."
    mkdir -p models
    cd whisper.cpp
    bash ./models/download-ggml-model.sh medium
    cd ..
    cp whisper.cpp/models/ggml-medium.bin models/
    success "Whisper model downloaded"
else
    success "Whisper model already exists"
fi

# Create necessary directories
info "Creating directories..."
mkdir -p temp notes models
success "Directories created"

# Initialize database
info "Initializing database..."
python init_db.py
success "Database initialized"

echo ""
echo "================================================"
echo -e "${GREEN}Setup Complete!${NC}"
echo "================================================"
echo ""
echo "To start the application:"
echo ""
echo "  1. Activate the virtual environment:"
echo "     source venv/bin/activate"
echo ""
echo "  2. Run the application:"
echo "     python app.py"
echo ""
echo "  3. Open your browser to:"
echo "     http://localhost:5000"
echo ""
echo "================================================"
