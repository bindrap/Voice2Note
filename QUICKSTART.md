# Quick Start Guide

Get Voice2Note up and running in 10 minutes!

## Prerequisites

Install these first:

1. **Python 3.8+**
   ```bash
   python3 --version  # Check if installed
   ```

2. **FFmpeg**
   ```bash
   # Ubuntu/Debian/WSL
   sudo apt update && sudo apt install ffmpeg

   # macOS
   brew install ffmpeg
   ```

## Automated Setup (Recommended)

### Linux/macOS/WSL

```bash
# Run the setup script
bash setup.sh
```

This will automatically:
- Create virtual environment
- Install Python dependencies
- Clone and build whisper.cpp
- Download Whisper model
- Initialize database

### Windows (Command Prompt)

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python init_db.py
```

Then manually install whisper.cpp (see Manual Setup below).

## Manual Setup

If the automated setup doesn't work:

### 1. Install Python Dependencies

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Install whisper.cpp

```bash
# Clone repository
git clone https://github.com/ggml-org/whisper.cpp.git
cd whisper.cpp

# Build
cmake -B build
cmake --build build -j --config Release

# Download model (choose one)
bash ./models/download-ggml-model.sh base    # Fast, 142MB
bash ./models/download-ggml-model.sh medium  # Recommended, 1.5GB

cd ..
```

### 3. Update Configuration

Edit `config.py` and update these paths:

```python
WHISPER_PATH = './whisper.cpp/build/bin/whisper-cli'
WHISPER_MODEL_PATH = './whisper.cpp/models/ggml-medium.bin'
```

### 4. Initialize Database

```bash
python init_db.py
```

## Running the Application

```bash
# Activate virtual environment (if not already activated)
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Start the server
python app.py
```

Open your browser to: **http://localhost:5000**

## First Use

### Test with YouTube

1. Go to http://localhost:5000
2. Paste this short test video: `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
3. Click "Process Video"
4. Wait 5-10 minutes (depending on your CPU)
5. View your generated notes!

### Test with Local File

1. Record a short voice memo or use an existing video
2. Upload it via the web interface
3. Process and view notes

## Troubleshooting

### "whisper.cpp not found"

**Solution**: Update `WHISPER_PATH` in `config.py` to point to your whisper.cpp binary:

```bash
# Find where whisper-cli is located
find . -name "whisper-cli"

# Update config.py with the correct path
```

### "FFmpeg not found"

**Solution**: Install FFmpeg:
```bash
sudo apt install ffmpeg  # Ubuntu/Debian/WSL
brew install ffmpeg      # macOS
```

### "Ollama API error"

**Solution**: Check your internet connection. The Ollama API requires internet access.

### Processing is slow

**Solutions**:
- Use the `base` model instead of `medium` (edit `config.py`)
- Process shorter videos first
- Consider GPU acceleration (see README.md)

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore the [Processing History](http://localhost:5000/history) page
- Try different video lengths and sources
- Customize note generation prompts in `processors/note_generator.py`

## Getting Help

- Check [README.md](README.md) for full documentation
- Review [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) for technical details
- Check [WHISPER_GUIDE.md](WHISPER_GUIDE.md) for whisper.cpp tips

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | Dual-core | Quad-core or better |
| RAM | 4GB | 8GB+ |
| Storage | 5GB | 10GB+ |
| Internet | Required for Ollama API | Required for Ollama API |

## Performance Expectations

**Processing a 10-minute video:**
- Audio extraction: 10-30 seconds
- Transcription (base model): 5-10 minutes
- Transcription (medium model): 10-20 minutes
- Note generation: 30-60 seconds
- **Total: ~6-21 minutes**

**With GPU acceleration:**
- Transcription time can be reduced by 5-10x!

---

**Ready to start? Run `python app.py` and open http://localhost:5000** 🚀
