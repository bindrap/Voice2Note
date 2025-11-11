# Installation Guide

Complete step-by-step installation instructions for Voice2Note.

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Install Prerequisites](#install-prerequisites)
3. [Install Voice2Note](#install-voice2note)
4. [Install whisper.cpp](#install-whispercpp)
5. [Configure the Application](#configure-the-application)
6. [Verify Installation](#verify-installation)
7. [Common Issues](#common-issues)

## System Requirements

### Minimum Requirements
- **OS**: Linux, macOS, or Windows (WSL recommended)
- **CPU**: Dual-core processor (2 GHz or faster)
- **RAM**: 4GB
- **Storage**: 5GB free space
- **Python**: 3.8 or higher
- **Internet**: Required for Ollama API

### Recommended Requirements
- **CPU**: Quad-core processor (3 GHz or faster)
- **RAM**: 8GB or more
- **Storage**: 10GB+ free space
- **GPU**: NVIDIA GPU with CUDA support (optional, for faster transcription)

## Install Prerequisites

### Ubuntu/Debian/WSL

```bash
# Update package list
sudo apt update

# Install required packages
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    ffmpeg \
    git \
    cmake \
    build-essential

# Verify installations
python3 --version
ffmpeg -version
git --version
cmake --version
```

### macOS

```bash
# Install Homebrew if not installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required packages
brew install python3 ffmpeg git cmake

# Verify installations
python3 --version
ffmpeg -version
git --version
cmake --version
```

### Windows

1. **Python 3.8+**: Download from [python.org](https://www.python.org/downloads/)
2. **FFmpeg**: Download from [ffmpeg.org](https://ffmpeg.org/download.html)
   - Extract and add to PATH
3. **Git**: Download from [git-scm.com](https://git-scm.com/download/win)
4. **CMake**: Download from [cmake.org](https://cmake.org/download/)

**OR use WSL (Recommended)**:
```bash
# Install WSL
wsl --install

# Follow Ubuntu/Debian instructions above
```

## Install Voice2Note

### Option 1: Automated Setup (Recommended)

```bash
# Navigate to project directory
cd /mnt/c/Users/bindrap/Documents/Voice2Note

# Run setup script
bash setup.sh
```

The setup script will:
- ✓ Create Python virtual environment
- ✓ Install Python dependencies
- ✓ Clone and build whisper.cpp
- ✓ Download Whisper model
- ✓ Initialize database
- ✓ Create necessary directories

**After setup completes**, skip to [Verify Installation](#verify-installation).

### Option 2: Manual Setup

#### Step 1: Create Virtual Environment

```bash
cd /mnt/c/Users/bindrap/Documents/Voice2Note

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # Linux/macOS
# OR
venv\Scripts\activate     # Windows
```

#### Step 2: Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

You should see:
```
Successfully installed flask-3.0.0 yt-dlp-2024.3.10 ollama-0.1.6 ...
```

#### Step 3: Create Directories

```bash
mkdir -p temp notes models
```

## Install whisper.cpp

### Clone Repository

```bash
git clone https://github.com/ggml-org/whisper.cpp.git
cd whisper.cpp
```

### Build whisper.cpp

#### Standard Build (CPU only)

```bash
cmake -B build
cmake --build build -j --config Release
```

#### With GPU Support (NVIDIA CUDA)

```bash
cmake -B build -DGGML_CUDA=1
cmake --build build -j --config Release
```

#### With GPU Support (Apple Silicon)

```bash
cmake -B build -DWHISPER_COREML=1
cmake --build build -j --config Release
```

### Download Whisper Model

Choose one model to download:

```bash
# Base model (fast, 142 MB, 90% accuracy)
bash ./models/download-ggml-model.sh base

# Medium model (recommended, 1.5 GB, 97% accuracy)
bash ./models/download-ggml-model.sh medium

# Large model (best quality, 2.9 GB, 98% accuracy)
bash ./models/download-ggml-model.sh large
```

### Copy Model to Project

```bash
# Copy the downloaded model to your project
cp models/ggml-medium.bin ../models/

# Return to project directory
cd ..
```

## Configure the Application

### Edit config.py

Open `config.py` and verify/update these settings:

```python
# Whisper paths
WHISPER_PATH = './whisper.cpp/build/bin/whisper-cli'
WHISPER_MODEL_PATH = './models/ggml-medium.bin'

# Model selection
WHISPER_MODEL = 'medium'  # or 'base', 'small', 'large'
```

### Set Environment Variables (Optional)

```bash
# Ollama API key (already set in config.py)
export OLLAMA_API_KEY="1728cbe73f944db7afa1a3c8f52d2f41.GzEVZ8ADdcDHwIxdbvKnqbXy"

# Flask secret key (for production)
export SECRET_KEY="your-random-secret-key"
```

### Initialize Database

```bash
python init_db.py
```

Expected output:
```
Database initialized at: ./voice2note.db
✓ Database initialized successfully!
```

## Verify Installation

### Check File Structure

Your directory should look like this:

```
Voice2Note/
├── app.py
├── config.py
├── requirements.txt
├── init_db.py
├── setup.sh
├── voice2note.db          ← Created after init_db.py
├── database/
│   ├── __init__.py
│   ├── db_manager.py
│   └── schema.sql
├── processors/
│   ├── __init__.py
│   ├── video_handler.py
│   ├── transcriber.py
│   └── note_generator.py
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── notes.html
│   └── history.html
├── static/
│   ├── css/style.css
│   └── js/app.js
├── whisper.cpp/
│   ├── build/bin/whisper-cli  ← Binary
│   └── models/ggml-*.bin      ← Models
├── temp/                   ← Empty directory
├── notes/                  ← Empty directory
└── models/
    └── ggml-medium.bin     ← Copied model
```

### Test Installation

```bash
# Activate virtual environment
source venv/bin/activate

# Test whisper.cpp
./whisper.cpp/build/bin/whisper-cli --help

# Test Python imports
python -c "from processors.video_handler import VideoHandler; print('✓ Imports OK')"

# Test Ollama connection (requires internet)
python -c "from ollama import Client; print('✓ Ollama library OK')"
```

### Start the Application

```bash
python app.py
```

You should see:
```
============================================================
Voice2Note Application Starting
============================================================
Database: ./voice2note.db
Temp directory: ./temp
Notes directory: ./notes
Whisper model: medium
Ollama model: gpt-oss:120b
============================================================

 * Running on http://0.0.0.0:5000
```

### Test Web Interface

Open your browser to: **http://localhost:5000**

You should see the Voice2Note homepage with upload options.

## Common Issues

### Issue: "whisper.cpp not found"

**Cause**: whisper.cpp binary not at expected location

**Solution**:
```bash
# Find the binary
find . -name whisper-cli

# Update config.py with the correct path
```

### Issue: "Whisper model not found"

**Cause**: Model not downloaded or in wrong location

**Solution**:
```bash
# Check if model exists
ls -lh models/

# If not found, download it
cd whisper.cpp
bash ./models/download-ggml-model.sh medium
cp models/ggml-medium.bin ../models/
cd ..
```

### Issue: "FFmpeg not found"

**Cause**: FFmpeg not installed or not in PATH

**Solution**:
```bash
# Check if installed
which ffmpeg

# If not found, install it
sudo apt install ffmpeg  # Ubuntu/Debian
brew install ffmpeg      # macOS
```

### Issue: "Cannot build whisper.cpp"

**Cause**: Missing build tools

**Solution**:
```bash
# Ubuntu/Debian
sudo apt install build-essential cmake

# macOS
xcode-select --install
brew install cmake
```

### Issue: "ModuleNotFoundError: No module named 'flask'"

**Cause**: Virtual environment not activated or dependencies not installed

**Solution**:
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Issue: "Permission denied: './setup.sh'"

**Cause**: Setup script not executable

**Solution**:
```bash
chmod +x setup.sh
bash setup.sh
```

## Next Steps

After successful installation:

1. **Read Quick Start**: See [QUICKSTART.md](QUICKSTART.md)
2. **Try a test video**: Process a short YouTube video
3. **Read full documentation**: See [README.md](README.md)
4. **Explore features**: Check out the History page

## Getting Help

If you encounter issues not covered here:

1. Check the [README.md](README.md) troubleshooting section
2. Verify all prerequisites are installed correctly
3. Check file permissions and paths in `config.py`
4. Review error messages carefully

## Performance Tips

### Use GPU Acceleration

If you have an NVIDIA GPU:
```bash
cd whisper.cpp
cmake -B build -DGGML_CUDA=1
cmake --build build -j --config Release
cd ..
```

### Use Smaller Model

For faster processing, use the `base` model:
```python
# In config.py
WHISPER_MODEL = 'base'
WHISPER_MODEL_PATH = './models/ggml-base.bin'
```

### Process Shorter Videos

Start with 5-10 minute videos while learning the system.

---

**Installation complete! Run `python app.py` to start using Voice2Note!** 🎉
