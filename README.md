# Voice2Note 🎥 → 📝

Convert videos and YouTube links into AI-enhanced markdown notes automatically.

## Features

### Core Functionality
- ✅ **YouTube Support**: Paste any YouTube URL to generate notes
- ✅ **Local Video Upload**: Upload video files (MP4, AVI, MOV, MKV, WebM)
- ✅ **Audio Files**: Also supports MP3, WAV, M4A
- ✅ **AI-Powered**: Uses Ollama for intelligent note generation
- ✅ **Fast Transcription**: Powered by whisper.cpp
- ✅ **Markdown Export**: Download notes in markdown format

### User Experience
- ✅ **User Accounts**: Secure authentication system with personal data isolation
- ✅ **Background Processing**: Videos process in background - navigate away anytime
- ✅ **Real-time Progress**: Granular progress tracking with detailed status updates
- ✅ **Video Management**: Cancel active processing, restart failed videos, delete entries
- ✅ **Storage Statistics**: Track total videos, notes, transcripts, and storage used
- ✅ **Processing History**: View all your processed videos with status indicators
- ✅ **Minimalistic UI**: Clean, modern interface with smooth animations
- ✅ **Responsive Design**: Works seamlessly on desktop and mobile

## Architecture

\`\`\`
Video/YouTube → Audio Extraction → Transcription → AI Notes → Database → Web UI
                (yt-dlp/ffmpeg)   (whisper.cpp)    (Ollama)    (SQLite)  (Flask)

Features:
- User authentication with session management  
- Background processing with threading
- Real-time status polling (2-second intervals)
- Cooperative cancellation with threading.Event()
- Granular progress tracking (5% → 100% with detailed sub-steps)
\`\`\`

## Quick Answer: Video Length Support

**With 24GB RAM (Oracle VM):**
- ✅ **1 hour**: ~20-60 minutes processing (excellent)
- ✅ **2 hours**: ~60-120 minutes processing (excellent)
- ✅ **6 hours**: ~3-6 hours processing (supported, long wait)
- ✅ **Unlimited**: No hard limit - scales linearly with video length

Use `large` or `medium` Whisper model for best results with 24GB RAM.

## Prerequisites

### System Requirements
- Python 3.8 or higher
- FFmpeg
- Git
- **RAM**: 4GB minimum (8GB recommended, 24GB optimal for large videos)
- **Disk**: 1GB + 100-500MB per hour of video processed

### Required Tools

1. **FFmpeg**: For audio/video processing
   \`\`\`bash
   # Ubuntu/Debian
   sudo apt update && sudo apt install ffmpeg

   # macOS  
   brew install ffmpeg

   # Windows
   # Download from https://ffmpeg.org/download.html
   \`\`\`

2. **whisper.cpp**: For audio transcription
   \`\`\`bash
   # Clone and build whisper.cpp
   git clone https://github.com/ggml-org/whisper.cpp.git
   cd whisper.cpp
   cmake -B build
   cmake --build build -j --config Release

   # Download the medium model (recommended)
   bash ./models/download-ggml-model.sh medium

   # Or download the base model (faster, less accurate)
   bash ./models/download-ggml-model.sh base

   # For 24GB RAM, use large model for best quality
   bash ./models/download-ggml-model.sh large
   \`\`\`

## Installation

### 1. Clone the Repository

\`\`\`bash
cd /path/to/Voice2Note
\`\`\`

### 2. Create Virtual Environment

\`\`\`bash
python3 -m venv venv

# Linux/macOS
source venv/bin/activate

# Windows
venv\\Scripts\\activate
\`\`\`

### 3. Install Python Dependencies

\`\`\`bash
pip install -r requirements.txt
\`\`\`

### 4. Configure whisper.cpp Path

Edit \`config.py\` and update the paths to match your whisper.cpp installation:

\`\`\`python
WHISPER_PATH = '/path/to/whisper.cpp/build/bin/whisper-cli'
WHISPER_MODEL_PATH = '/path/to/whisper.cpp/models/ggml-medium.bin'

# For 24GB RAM Oracle VM - use large model:
WHISPER_MODEL_PATH = '/path/to/whisper.cpp/models/ggml-large.bin'
\`\`\`

### 5. Set Environment Variables (Optional)

\`\`\`bash
# Ollama API key (already set in config.py, but can override)
export OLLAMA_API_KEY="your-api-key"

# Flask secret key (for production)
export SECRET_KEY="your-secret-key"
\`\`\`

### 6. Initialize Database

\`\`\`bash
python init_db.py
\`\`\`

You should see:
\`\`\`
✓ Database initialized successfully!
\`\`\`

## Running the Application

### Development Mode

\`\`\`bash
python app.py
\`\`\`

The application will start on \`http://localhost:5000\`

### Production Mode

For production, use a WSGI server like Gunicorn:

\`\`\`bash
pip install gunicorn

gunicorn -w 4 -b 0.0.0.0:5000 app:app
\`\`\`

Or use the provided systemd service (Linux):

\`\`\`bash
# Copy service file
sudo cp voice2note.service /etc/systemd/system/

# Edit the service file to match your paths
sudo nano /etc/systemd/system/voice2note.service

# Enable and start
sudo systemctl enable voice2note
sudo systemctl start voice2note
\`\`\`

## Usage

### First Time Setup

1. Open \`http://localhost:5000\`
2. Click "Register" to create your account
3. Enter username, email, and password
4. Login with your credentials

### Processing a YouTube Video

1. Login to your account
2. Paste a YouTube URL in the input field
3. Click "Process Video"
4. **Processing happens in background** - you can navigate away!
5. Check "History" to monitor progress with real-time updates
6. View or download your notes when complete

### Uploading a Local Video

1. Login to your account
2. Click "Choose a file" or drag & drop a video file
3. Click "Process Video"
4. **Processing continues in background** - check History page anytime
5. View or download your notes when complete

### Managing Videos

**In the History page, you can:**
- **Monitor Progress**: Real-time progress bars with detailed status (e.g., "55% • Transcribing audio...")
- **Cancel Processing**: Stop videos currently being processed
- **Restart Failed**: Retry processing for failed or cancelled YouTube videos
- **Delete Videos**: Remove any video and its associated data
- **View Statistics**: See total videos, storage used, and processing history

### Processing Time Estimates

| Video Length | Whisper Model | Processing Time | Status |
|--------------|---------------|-----------------|--------|
| 10 minutes   | base          | ~5-10 minutes   | ✅ Fast |
| 10 minutes   | medium        | ~10-20 minutes  | ✅ Recommended |
| 1 hour       | base          | ~30-60 minutes  | ✅ Good |
| 1 hour       | medium        | ~60-120 minutes | ✅ Quality |
| 1 hour       | large (24GB)  | ~30-60 minutes  | ✅ Excellent |
| 2 hours      | base          | ~60-120 minutes | ✅ Supported |
| 2 hours      | medium        | ~2-4 hours      | ✅ Supported |
| 2 hours      | large (24GB)  | ~60-120 minutes | ✅ Excellent |
| 6 hours      | base          | ~3-6 hours      | ⚠️ Long wait |
| 6 hours      | medium        | ~6-12 hours     | ⚠️ Very long |
| 6 hours      | large (24GB)  | ~3-6 hours      | ✅ Feasible |

*Times are for CPU processing. GPU acceleration can be 5-10x faster.*

**Maximum Video Length:**
- **Technical limit**: No hard limit
- **Practical considerations**:
  - **RAM requirements**: 4-8GB for base, 8-16GB for medium, 16-24GB for large
  - **Disk space**: ~100-500MB per hour of video for temporary audio files
  - **Processing time**: Scales linearly (2x length = 2x time)
  - **API token limits**: Very long transcripts (>6 hours) may need chunking

---

**Happy Note-Taking! 📝**

## Project Structure

\`\`\`
voice2note/
├── app.py                      # Main Flask application with auth & threading
├── config.py                   # Configuration
├── requirements.txt            # Python dependencies
├── init_db.py                  # Database initialization
├── reset_database.py           # Database reset utility
│
├── database/
│   ├── schema.sql             # Database schema (with users table)
│   └── db_manager.py          # Database operations & user management
│
├── processors/
│   ├── video_handler.py       # Video/audio extraction (yt-dlp/ffmpeg)
│   ├── transcriber.py         # Whisper.cpp integration
│   └── note_generator.py      # Ollama note generation with streaming
│
├── templates/
│   ├── base.html              # Base template with navbar
│   ├── index.html             # Main upload page with stats
│   ├── notes.html             # Notes viewer with markdown rendering
│   ├── history.html           # Processing history with real-time updates
│   ├── login.html             # User login page
│   ├── register.html          # User registration page
│   └── profile.html           # User profile with statistics
│
├── static/
│   ├── css/
│   │   └── style.css          # Minimalistic styling with animations
│   ├── js/
│   │   └── app.js             # JavaScript utilities
│   └── favicon.svg            # Application favicon
│
├── temp/                       # Temporary audio/video files
└── voice2note.db              # SQLite database
\`\`\`

## Configuration

### Whisper Model Selection

Edit \`config.py\` to change the Whisper model:

\`\`\`python
WHISPER_MODEL = 'base'    # Fast, good accuracy (142 MB)
WHISPER_MODEL = 'small'   # Better accuracy (466 MB)
WHISPER_MODEL = 'medium'  # Best balance (1.5 GB) - RECOMMENDED for 8GB RAM
WHISPER_MODEL = 'large'   # Best accuracy (2.9 GB) - RECOMMENDED for 24GB RAM
\`\`\`

### Ollama Configuration

The Ollama API key is already configured in \`config.py\`. To use a different model:

\`\`\`python
OLLAMA_MODEL = 'gpt-oss:120b'  # Current model
\`\`\`

### File Size Limits

Default maximum file size is 500MB. To change:

\`\`\`python
MAX_CONTENT_LENGTH = 1000 * 1024 * 1024  # 1GB
\`\`\`

## Performance Optimization

### Optimal Configurations by Hardware

#### High-Performance Setup (24GB+ RAM) - Oracle VM / Server
**Perfect for: Long videos (6+ hours), maximum quality, parallel processing**

\`\`\`python
# config.py
WHISPER_MODEL = 'large'  # Best accuracy (2.9GB)
# or 'medium' for faster processing (1.5GB)
\`\`\`

**Capabilities with 24GB RAM:**
- ✅ Process 6+ hour videos with ease
- ✅ Use large Whisper model for best accuracy
- ✅ Handle multiple videos simultaneously
- ✅ Run local Ollama models (fully offline)
- ✅ No memory constraints

**Processing Performance (24GB RAM, multi-core CPU):**
| Video Length | Model  | Processing Time | Quality |
|--------------|--------|-----------------|---------|
| 1 hour       | large  | ~30-60 min      | Excellent |
| 2 hours      | large  | ~60-120 min     | Excellent |
| 6 hours      | large  | ~3-6 hours      | Excellent |
| 1 hour       | medium | ~20-40 min      | Very Good |

#### Standard Setup (8GB RAM) - Laptop
\`\`\`python
WHISPER_MODEL = 'medium'  # Recommended (1.5GB)
\`\`\`

#### Low-Resource Setup (4GB RAM) - Entry-level
\`\`\`python
WHISPER_MODEL = 'base'  # Fast and efficient (142MB)
\`\`\`

### GPU Acceleration

For much faster transcription, build whisper.cpp with GPU support:

#### NVIDIA GPU (CUDA)
\`\`\`bash
cd whisper.cpp
cmake -B build -DGGML_CUDA=1
cmake --build build -j --config Release
\`\`\`

#### Apple Silicon (Metal)
\`\`\`bash
cd whisper.cpp
cmake -B build -DWHISPER_COREML=1
cmake --build build -j --config Release
\`\`\`

### Model Quantization

Use quantized models for faster processing with slightly reduced accuracy:

\`\`\`bash
cd whisper.cpp
./build/bin/quantize models/ggml-medium.bin models/ggml-medium-q5_0.bin q5_0
\`\`\`

Update config.py:
\`\`\`python
WHISPER_MODEL_PATH = '/path/to/whisper.cpp/models/ggml-medium-q5_0.bin'
\`\`\`

## API Endpoints

### Authentication

**Register User**
\`\`\`http
POST /register
Content-Type: application/x-www-form-urlencoded

username=<username>&email=<email>&password=<password>&confirm_password=<password>
\`\`\`

**Login**
\`\`\`http
POST /login
Content-Type: application/x-www-form-urlencoded

username=<username>&password=<password>
\`\`\`

**Logout**
\`\`\`http
GET /logout
\`\`\`

**Get Profile**
\`\`\`http
GET /profile
\`\`\`

### Video Processing

**Process Video** (requires authentication)
\`\`\`http
POST /process
Content-Type: multipart/form-data

youtube_url=https://youtube.com/watch?v=...
OR
video_file=<file>

Response:
{
  "success": true,
  "video_id": 123,
  "message": "Processing started in background...",
  "processing": true
}
\`\`\`

**Get Processing Status** (requires authentication)
\`\`\`http
GET /status/<video_id>

Response:
{
  "status": "transcribing",
  "progress": 55,
  "error_message": null
}
\`\`\`

**Cancel Processing** (requires authentication)
\`\`\`http
POST /cancel/<video_id>

Response:
{
  "success": true,
  "message": "Processing cancelled"
}
\`\`\`

**Restart Processing** (requires authentication)
\`\`\`http
POST /restart/<video_id>

Response:
{
  "success": true,
  "video_id": 123,
  "message": "Processing restarted"
}
\`\`\`

**Delete Video** (requires authentication)
\`\`\`http
POST /delete/<video_id>

Response:
{
  "success": true,
  "message": "Video and all associated data deleted"
}
\`\`\`

### Notes & Data

**Get Notes** (requires authentication)
\`\`\`http
GET /notes/<video_id>
\`\`\`

**Download Notes** (requires authentication)
\`\`\`http
GET /download/<video_id>
\`\`\`

**Get All Videos** (requires authentication)
\`\`\`http
GET /api/videos

Response: Array of video objects with status, progress, etc.
\`\`\`

**Search Videos** (requires authentication)
\`\`\`http
GET /api/search?q=<query>
\`\`\`

### Processing States

Videos go through these states:
- \`pending\` (5%) - Queued for processing
- \`extracting\` (10-30%) - Extracting audio from video
- \`transcribing\` (30-60%) - Converting audio to text
- \`generating\` (60-100%) - Creating AI-enhanced notes
- \`completed\` (100%) - Notes ready
- \`failed\` - Processing error occurred
- \`cancelled\` - User cancelled processing

## Troubleshooting

### whisper.cpp Not Found

**Error**: \`whisper.cpp not found at /path/to/whisper.cpp\`

**Solution**:
1. Verify whisper.cpp is installed and built
2. Update \`WHISPER_PATH\` in \`config.py\` to the correct path
3. Ensure the binary is executable: \`chmod +x /path/to/whisper.cpp/build/bin/whisper-cli\`

### Whisper Model Not Found

**Error**: \`Whisper model not found at /path/to/model\`

**Solution**:
1. Download the model: \`cd whisper.cpp && bash ./models/download-ggml-model.sh medium\`
2. Update \`WHISPER_MODEL_PATH\` in \`config.py\`

### FFmpeg Not Found

**Error**: \`Failed to extract audio: ffmpeg not found\`

**Solution**: Install FFmpeg using your package manager (see Prerequisites)

### Ollama API Error

**Error**: \`Failed to generate notes: API error\`

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
5. For 24GB RAM systems: Use large model for best results

### Slow Processing

**Solutions**:
- Use a smaller Whisper model (\`base\` instead of \`medium\`)
- Enable GPU acceleration for whisper.cpp
- Use a machine with more CPU cores
- Process shorter videos
- For 24GB RAM: Upgrade to \`large\` model with more CPU cores

## FAQ

**Q: How long does processing take?**
A: Typically 2-5x the video length for transcription, plus 1-3 minutes for note generation. See processing time table above for details.

**Q: Can I process videos longer than 1 hour?**
A: Yes! The system supports 1-6+ hour videos. Processing scales linearly: 2-hour videos take ~2-4 hours with medium model on CPU. With 24GB RAM and large model, you can efficiently process 6+ hour videos.

**Q: Can I navigate away while processing?**
A: Yes! Processing happens in the background. You can close the tab, navigate away, or even restart your browser. Check the History page anytime to see progress.

**Q: Can I cancel a video that's processing?**
A: Yes! Go to History page and click "Cancel" on any processing video. You can also restart failed or cancelled YouTube videos.

**Q: Is my data private?**
A: Transcription happens locally on your machine. Only the transcript is sent to Ollama API for note generation. Each user's data is isolated - you only see your own videos.

**Q: How is user data protected?**
A: Passwords are hashed with SHA-256. Session-based authentication keeps you logged in. Each user can only access their own videos and notes.

**Q: Can I use a different AI model?**
A: Yes, you can modify \`note_generator.py\` to use Claude, GPT-4, or local Ollama models. The Ollama API key is already configured.

**Q: Does it work offline?**
A: Transcription works fully offline. Note generation requires internet for Ollama API, or you can run local Ollama for fully offline operation.

**Q: What video formats are supported?**
A: **Video**: MP4, AVI, MOV, MKV, WebM, FLV, WMV | **Audio**: MP3, WAV, M4A

**Q: What happens if processing fails?**
A: Failed videos show in History with a "Failed" status. For YouTube videos, you can click "Restart" to try again. You can also delete failed entries.

**Q: How much storage does it use?**
A: Check your Profile or homepage for storage statistics. Approximately 100-500MB per hour of video for audio files, plus database entries for notes and transcripts.

**Q: What's the best setup for an Oracle VM with 24GB RAM?**
A: Use the \`large\` Whisper model for best accuracy. You can easily process 6+ hour videos, handle multiple videos simultaneously, and optionally run local Ollama models for fully offline operation.

## Roadmap

### Phase 1 - MVP ✅ COMPLETE
- [x] YouTube URL processing
- [x] Local file upload
- [x] Audio transcription (whisper.cpp)
- [x] AI note generation (Ollama)
- [x] Web interface
- [x] Processing history
- [x] User authentication system
- [x] Background processing with threading
- [x] Real-time progress tracking (polling-based)
- [x] Video management (cancel/restart/delete)
- [x] Storage statistics
- [x] Minimalistic UI design

### Phase 2 - Enhancement (In Progress)
- [x] Granular progress updates
- [x] Cooperative cancellation system
- [ ] Real-time progress with WebSockets (upgrade from polling)
- [ ] Note editing interface
- [ ] Multiple export formats (PDF, DOCX)
- [ ] Batch processing (multiple videos at once)
- [ ] Custom note templates
- [ ] Advanced search functionality
- [ ] Email notifications on completion

### Phase 3 - Advanced Features
- [ ] Chapter detection from video/description
- [ ] Speaker identification (diarization)
- [ ] Multi-language support (auto-detect)
- [ ] Video timestamp linking in notes
- [ ] Integration with note-taking apps (Notion, Obsidian, Evernote)
- [ ] Mobile app (iOS/Android)
- [ ] Browser extension for quick captures
- [ ] Collaborative notes (sharing with teams)
- [ ] API rate limiting and quotas
- [ ] Admin dashboard

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

---

**Happy Note-Taking! 📝**
