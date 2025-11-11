# Voice2Note 🎥 → 📝

Convert videos and YouTube links into AI-enhanced markdown notes automatically.

## Features

- ✅ **YouTube Support**: Paste any YouTube URL to generate notes
- ✅ **Local Video Upload**: Upload video files (MP4, AVI, MOV, MKV, WebM)
- ✅ **Audio Files**: Also supports MP3, WAV, M4A
- ✅ **AI-Powered**: Uses Ollama for intelligent note generation
- ✅ **Fast Transcription**: Powered by whisper.cpp
- ✅ **Markdown Export**: Download notes in markdown format
- ✅ **Processing History**: Track all your processed videos
- ✅ **Responsive UI**: Works on desktop and mobile

## Architecture

```
Video/YouTube → Audio Extraction → Transcription → AI Notes → Database → Web UI
                (yt-dlp/ffmpeg)   (whisper.cpp)    (Ollama)    (SQLite)  (Flask)
```

## Prerequisites

### System Requirements
- Python 3.8 or higher
- FFmpeg
- Git
- 4GB RAM minimum (8GB recommended for medium Whisper model)

### Required Tools

1. **FFmpeg**: For audio/video processing
   ```bash
   # Ubuntu/Debian
   sudo apt update && sudo apt install ffmpeg

   # macOS
   brew install ffmpeg

   # Windows
   # Download from https://ffmpeg.org/download.html
   ```

2. **whisper.cpp**: For audio transcription
   ```bash
   # Clone and build whisper.cpp
   git clone https://github.com/ggml-org/whisper.cpp.git
   cd whisper.cpp
   cmake -B build
   cmake --build build -j --config Release

   # Download the medium model (recommended)
   bash ./models/download-ggml-model.sh medium

   # Or download the base model (faster, less accurate)
   bash ./models/download-ggml-model.sh base
   ```

## Installation

### 1. Clone the Repository

```bash
cd /path/to/Voice2Note
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv

# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure whisper.cpp Path

Edit `config.py` and update the paths to match your whisper.cpp installation:

```python
WHISPER_PATH = '/path/to/whisper.cpp/build/bin/whisper-cli'
WHISPER_MODEL_PATH = '/path/to/whisper.cpp/models/ggml-medium.bin'
```

### 5. Set Environment Variables (Optional)

```bash
# Ollama API key (already set in config.py, but can override)
export OLLAMA_API_KEY="your-api-key"

# Flask secret key (for production)
export SECRET_KEY="your-secret-key"
```

### 6. Initialize Database

```bash
python init_db.py
```

You should see:
```
✓ Database initialized successfully!
```

## Running the Application

### Development Mode

```bash
python app.py
```

The application will start on `http://localhost:5000`

### Production Mode

For production, use a WSGI server like Gunicorn:

```bash
pip install gunicorn

gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

Or use the provided systemd service (Linux):

```bash
# Copy service file
sudo cp voice2note.service /etc/systemd/system/

# Edit the service file to match your paths
sudo nano /etc/systemd/system/voice2note.service

# Enable and start
sudo systemctl enable voice2note
sudo systemctl start voice2note
```

## Usage

### Processing a YouTube Video

1. Open `http://localhost:5000`
2. Paste a YouTube URL in the input field
3. Click "Process Video"
4. Wait for processing to complete (this can take several minutes)
5. View or download your notes

### Uploading a Local Video

1. Open `http://localhost:5000`
2. Click "Choose a file" or drag & drop a video file
3. Click "Process Video"
4. Wait for processing to complete
5. View or download your notes

### Processing Time Estimates

| Video Length | Whisper Model | Processing Time |
|--------------|---------------|-----------------|
| 10 minutes   | base          | ~5-10 minutes   |
| 10 minutes   | medium        | ~10-20 minutes  |
| 1 hour       | base          | ~30-60 minutes  |
| 1 hour       | medium        | ~60-120 minutes |

*Times are for CPU processing. GPU acceleration can be 5-10x faster.*

## Project Structure

```
voice2note/
├── app.py                      # Main Flask application
├── config.py                   # Configuration
├── requirements.txt            # Python dependencies
├── init_db.py                  # Database initialization
│
├── database/
│   ├── schema.sql             # Database schema
│   └── db_manager.py          # Database operations
│
├── processors/
│   ├── video_handler.py       # Video/audio extraction
│   ├── transcriber.py         # Whisper.cpp integration
│   └── note_generator.py      # Ollama note generation
│
├── templates/
│   ├── base.html              # Base template
│   ├── index.html             # Main upload page
│   ├── notes.html             # Notes viewer
│   └── history.html           # Processing history
│
├── static/
│   ├── css/
│   │   └── style.css          # Styling
│   └── js/
│       └── app.js             # JavaScript
│
├── temp/                       # Temporary files
├── notes/                      # Saved notes
└── models/                     # Whisper models
```

## Configuration

### Whisper Model Selection

Edit `config.py` to change the Whisper model:

```python
WHISPER_MODEL = 'base'    # Fast, good accuracy (142 MB)
WHISPER_MODEL = 'small'   # Better accuracy (466 MB)
WHISPER_MODEL = 'medium'  # Best balance (1.5 GB) - RECOMMENDED
WHISPER_MODEL = 'large'   # Best accuracy (2.9 GB)
```

### Ollama Configuration

The Ollama API key is already configured in `config.py`. To use a different model:

```python
OLLAMA_MODEL = 'gpt-oss:120b'  # Current model
```

### File Size Limits

Default maximum file size is 500MB. To change:

```python
MAX_CONTENT_LENGTH = 1000 * 1024 * 1024  # 1GB
```

## Troubleshooting

### whisper.cpp Not Found

**Error**: `whisper.cpp not found at /path/to/whisper.cpp`

**Solution**:
1. Verify whisper.cpp is installed and built
2. Update `WHISPER_PATH` in `config.py` to the correct path
3. Ensure the binary is executable: `chmod +x /path/to/whisper.cpp/build/bin/whisper-cli`

### Whisper Model Not Found

**Error**: `Whisper model not found at /path/to/model`

**Solution**:
1. Download the model: `cd whisper.cpp && bash ./models/download-ggml-model.sh medium`
2. Update `WHISPER_MODEL_PATH` in `config.py`

### FFmpeg Not Found

**Error**: `Failed to extract audio: ffmpeg not found`

**Solution**: Install FFmpeg using your package manager (see Prerequisites)

### Ollama API Error

**Error**: `Failed to generate notes: API error`

**Solution**:
1. Verify the API key is correct
2. Check your internet connection
3. Verify the Ollama API is accessible

### Out of Memory

**Error**: Process killed or memory errors

**Solution**:
1. Use a smaller Whisper model (base instead of medium)
2. Close other applications
3. Process shorter videos
4. Add more RAM to your system

### Slow Processing

**Solutions**:
- Use a smaller Whisper model (`base` instead of `medium`)
- Enable GPU acceleration for whisper.cpp
- Use a machine with more CPU cores
- Process shorter videos

## API Endpoints

### Process Video
```http
POST /process
Content-Type: multipart/form-data

youtube_url=https://youtube.com/watch?v=...
OR
video_file=<file>
```

### Get Notes
```http
GET /notes/<video_id>
```

### Download Notes
```http
GET /download/<video_id>
```

### Get Processing Status
```http
GET /status/<video_id>
```

### Get All Videos
```http
GET /api/videos
```

### Search Videos
```http
GET /api/search?q=<query>
```

## Development

### Running Tests

```bash
# TODO: Add tests
pytest tests/
```

### Database Reset

To reset the database:

```bash
rm voice2note.db
python init_db.py
```

### Debugging

Enable debug mode in `config.py`:

```python
DEBUG = True
```

View logs:
```bash
# If running as systemd service
sudo journalctl -u voice2note -f
```

## Performance Optimization

### GPU Acceleration

For much faster transcription, build whisper.cpp with GPU support:

#### NVIDIA GPU (CUDA)
```bash
cd whisper.cpp
cmake -B build -DGGML_CUDA=1
cmake --build build -j --config Release
```

#### Apple Silicon (Metal)
```bash
cd whisper.cpp
cmake -B build -DWHISPER_COREML=1
cmake --build build -j --config Release
```

### Model Quantization

Use quantized models for faster processing with slightly reduced accuracy:

```bash
cd whisper.cpp
./build/bin/quantize models/ggml-medium.bin models/ggml-medium-q5_0.bin q5_0
```

Update config.py:
```python
WHISPER_MODEL_PATH = '/path/to/whisper.cpp/models/ggml-medium-q5_0.bin'
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - See LICENSE file for details

## Credits

- **whisper.cpp**: https://github.com/ggml-org/whisper.cpp
- **yt-dlp**: https://github.com/yt-dlp/yt-dlp
- **Ollama**: https://ollama.com
- **Flask**: https://flask.palletsprojects.com

## Support

For issues and questions:
- Check the troubleshooting section above
- Review existing issues in the issue tracker
- Create a new issue with details about your problem

## Roadmap

### Phase 1 (Current) - MVP
- [x] YouTube URL processing
- [x] Local file upload
- [x] Audio transcription
- [x] AI note generation
- [x] Web interface
- [x] Processing history

### Phase 2 - Enhancement
- [ ] Real-time progress tracking with WebSocket
- [ ] Note editing interface
- [ ] Multiple export formats (PDF, DOCX)
- [ ] Batch processing
- [ ] Custom note templates
- [ ] Search functionality

### Phase 3 - Advanced
- [ ] Chapter detection
- [ ] Speaker identification
- [ ] Multi-language support
- [ ] Video timestamp linking
- [ ] Integration with note-taking apps (Notion, Obsidian)
- [ ] Mobile app

## FAQ

**Q: How long does processing take?**
A: Typically 2-5x the video length for transcription, plus 1-3 minutes for note generation.

**Q: Can I process videos longer than 1 hour?**
A: Yes, but processing will take proportionally longer. Consider using a smaller Whisper model or GPU acceleration.

**Q: Is my data private?**
A: Transcription happens locally on your machine. Only the transcript is sent to Ollama API for note generation.

**Q: Can I use a different AI model?**
A: Yes, you can modify `note_generator.py` to use Claude, GPT-4, or local models via Ollama.

**Q: Does it work offline?**
A: Transcription works offline, but note generation requires internet access to Ollama API. You can use local Ollama for fully offline operation.

**Q: What video formats are supported?**
A: MP4, AVI, MOV, MKV, WebM, FLV, WMV, and audio formats: MP3, WAV, M4A

---

**Happy Note-Taking! 📝**
#   V o i c e 2 N o t e  
 