# Voice2Note - Video/Audio to AI-Enhanced Notes

## Project Goal
Create a web app where users can upload videos or provide YouTube links to generate AI-enhanced notes using Ollama.

## Ollama API Configuration
```python
import os
from ollama import Client

client = Client(
    host="https://ollama.com",
    headers={'Authorization': 'Bearer ' + os.environ.get('OLLAMA_API_KEY')}
)

# API Key: 1728cbe73f944db7afa1a3c8f52d2f41.GzEVZ8ADdcDHwIxdbvKnqbXy

messages = [
  {
    'role': 'user',
    'content': 'Why is the sky blue?',
  },
]

for part in client.chat('gpt-oss:120b', messages=messages, stream=True):
  print(part['message']['content'], end='', flush=True)
```

## Core Architecture
```
Input (YouTube URL or Local Video)
  ↓
Video Source Handler
  ├→ YouTube: yt-dlp → extract audio + metadata
  └→ Local: ffmpeg → extract audio
  ↓
Whisper.cpp Transcription (with word timestamps)
  ↓
AI Processing (Ollama/Azure OpenAI)
  - Extract structured data
  - Create organized notes
  ↓
Storage (SQLite/Postgres)
  ↓
Note Generator (Markdown output)
  ↓
Web UI (Flask) - Browse, search, download
```

## Technology Stack

### Core Components
- **whisper.cpp**: Audio transcription with timestamps
- **yt-dlp**: YouTube video/audio download
- **ffmpeg**: Audio extraction from local videos
- **Ollama**: AI processing for note generation
- **Flask**: Web interface
- **SQLite**: Database for storage
- **Python**: Orchestration layer

### Required Libraries
```python
# requirements.txt
yt-dlp
ollama
requests
flask
markdown
```

## Implementation Components

### 1. Video Source Handler
```python
import yt_dlp
import os
import subprocess

def download_youtube_audio(url, output_path):
    """Download audio from YouTube video"""
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
        'outtmpl': f'{output_path}/%(id)s.%(ext)s',
        'quiet': False,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return {
            'audio_path': f"{output_path}/{info['id']}.wav",
            'title': info['title'],
            'channel': info['uploader'],
            'duration': info['duration'],
            'video_id': info['id'],
            'url': url,
            'description': info.get('description', ''),
            'chapters': info.get('chapters', []),
        }

def extract_local_audio(video_path, output_path):
    """Extract audio from local video file"""
    audio_path = f"{output_path}/{os.path.basename(video_path)}.wav"
    subprocess.run([
        'ffmpeg', '-i', video_path,
        '-vn', '-acodec', 'pcm_s16le',
        '-ar', '16000', '-ac', '1',
        audio_path
    ])
    return {
        'audio_path': audio_path,
        'title': os.path.basename(video_path),
        'source': 'local',
    }

def process_video(source, output_path='./temp'):
    """Handle both YouTube and local files"""
    if 'youtube.com' in source or 'youtu.be' in source:
        return download_youtube_audio(source, output_path)
    else:
        return extract_local_audio(source, output_path)
```

### 2. Whisper Transcription
```python
import subprocess
import json

def transcribe_with_whisper(audio_path, model='medium'):
    """
    Transcribe audio using whisper.cpp
    Returns transcription with word-level timestamps
    """
    output_json = audio_path.replace('.wav', '.json')

    subprocess.run([
        './whisper.cpp/main',
        '-m', f'./models/ggml-{model}.bin',
        '-f', audio_path,
        '--output-json',
        '--word-timestamps',
        '-oj', output_json
    ])

    with open(output_json, 'r') as f:
        return json.load(f)

def chunk_transcription(transcription, chunk_size=5000):
    """Split long transcriptions into processable chunks"""
    chunks = []
    current_chunk = []
    current_length = 0

    for segment in transcription['transcription']:
        segment_text = segment['text']
        if current_length + len(segment_text) > chunk_size:
            chunks.append(current_chunk)
            current_chunk = [segment]
            current_length = len(segment_text)
        else:
            current_chunk.append(segment)
            current_length += len(segment_text)

    if current_chunk:
        chunks.append(current_chunk)

    return chunks
```

### 3. AI Processing with Ollama
```python
from ollama import Client
import os

def generate_notes(transcription_text, metadata):
    """
    Generate structured notes using Ollama
    """
    client = Client(
        host="https://ollama.com",
        headers={'Authorization': 'Bearer ' + os.environ.get('OLLAMA_API_KEY')}
    )

    prompt = f"""
You are creating structured notes from a video transcript.

Video Title: {metadata['title']}
Source: {metadata.get('channel', 'Unknown')}

Create comprehensive markdown notes with:
1. Clear headings and subheadings
2. Main concepts and key points
3. Step-by-step explanations where applicable
4. Important details and context
5. Timestamps for reference
6. Summary/Key Takeaways section

Transcript:
{transcription_text}

Generate well-structured markdown notes:
"""

    notes = ""
    for part in client.chat('gpt-oss:120b',
                           messages=[{'role': 'user', 'content': prompt}],
                           stream=True):
        notes += part['message']['content']

    return notes
```

### 4. Database Schema
```sql
-- notes.sql

CREATE TABLE videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_url TEXT,
    title TEXT NOT NULL,
    creator TEXT,
    duration INTEGER,
    upload_date DATE,
    processed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id INTEGER,
    content TEXT NOT NULL,
    format TEXT DEFAULT 'markdown',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (video_id) REFERENCES videos(id)
);

CREATE TABLE transcripts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id INTEGER,
    transcript_text TEXT NOT NULL,
    timestamps TEXT, -- JSON array
    FOREIGN KEY (video_id) REFERENCES videos(id)
);

-- Indexes for fast lookups
CREATE INDEX idx_videos_title ON videos(title);
CREATE INDEX idx_notes_video ON notes(video_id);
```

### 5. Flask Web Application
```python
from flask import Flask, render_template, request, jsonify, send_file
import sqlite3
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_video_endpoint():
    """Handle video processing request"""
    source = request.form.get('source')  # URL or file

    try:
        # 1. Download/extract audio
        metadata = process_video(source)

        # 2. Transcribe
        transcription = transcribe_with_whisper(metadata['audio_path'])

        # 3. Generate notes with Ollama
        notes = generate_notes(transcription, metadata)

        # 4. Store in database
        video_id = store_video(metadata)
        store_notes(notes, video_id)
        store_transcript(transcription, video_id)

        return jsonify({
            'success': True,
            'video_id': video_id,
            'notes_preview': notes[:500]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/notes/<int:video_id>')
def view_notes(video_id):
    """View generated notes"""
    conn = sqlite3.connect('voice2note.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT v.title, v.creator, n.content
        FROM notes n
        JOIN videos v ON n.video_id = v.id
        WHERE v.id = ?
    """, (video_id,))
    result = cursor.fetchone()
    conn.close()

    if result:
        return render_template('notes.html',
                             title=result[0],
                             creator=result[1],
                             content=result[2])
    return "Notes not found", 404

@app.route('/download/<int:video_id>')
def download_notes(video_id):
    """Download notes as markdown file"""
    conn = sqlite3.connect('voice2note.db')
    cursor = conn.cursor()
    cursor.execute("SELECT content FROM notes WHERE video_id = ?", (video_id,))
    result = cursor.fetchone()
    conn.close()

    if result:
        # Save to temp file and send
        temp_file = f'/tmp/notes_{video_id}.md'
        with open(temp_file, 'w') as f:
            f.write(result[0])
        return send_file(temp_file, as_attachment=True, download_name='notes.md')
    return "Notes not found", 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

## Project Structure
```
voice2note/
├── app.py                 # Flask application
├── requirements.txt       # Python dependencies
├── config.py             # Configuration (API keys, paths)
├── models/               # Whisper models
│   └── ggml-medium.bin
├── processors/
│   ├── video_handler.py  # YouTube/local video processing
│   ├── transcriber.py    # Whisper integration
│   └── note_generator.py # Note generation with Ollama
├── database/
│   ├── schema.sql        # Database schema
│   └── db_manager.py     # Database operations
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
├── templates/
│   ├── index.html        # Main upload interface
│   ├── notes.html        # Notes viewer
│   └── history.html      # Processing history
├── temp/                 # Temporary audio files
└── notes/                # Generated markdown notes
```

## Configuration
```python
# config.py

import os

class Config:
    # Paths
    TEMP_DIR = './temp'
    NOTES_DIR = './notes'
    MODELS_DIR = './models'
    DATABASE_PATH = './voice2note.db'

    # Whisper
    WHISPER_MODEL = 'medium'
    WHISPER_PATH = './whisper.cpp/main'

    # Ollama
    OLLAMA_API_KEY = os.getenv('OLLAMA_API_KEY', '1728cbe73f944db7afa1a3c8f52d2f41.GzEVZ8ADdcDHwIxdbvKnqbXy')
    OLLAMA_HOST = 'https://ollama.com'
    OLLAMA_MODEL = 'gpt-oss:120b'

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-prod')
    DEBUG = True
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB max file size
```

## Features to Implement

### Phase 1: Core Functionality (MVP)
- [ ] Video upload interface
- [ ] YouTube URL input
- [ ] Audio extraction (yt-dlp + ffmpeg)
- [ ] Audio transcription (whisper.cpp)
- [ ] AI note generation (Ollama)
- [ ] Display generated notes
- [ ] Download notes as markdown

### Phase 2: Enhancement
- [ ] Processing progress indicator
- [ ] History of processed videos
- [ ] Search functionality
- [ ] Note editing interface
- [ ] Multiple output formats (PDF, DOCX)
- [ ] Customizable note styles/templates

### Phase 3: Advanced Features
- [ ] Batch processing
- [ ] Chapter detection for longer videos
- [ ] Multi-language support
- [ ] Speaker identification
- [ ] Video timestamp links in notes
- [ ] Export to note-taking apps (Notion, Obsidian)

## Installation & Setup

### Prerequisites
```bash
# Install system dependencies
sudo apt update
sudo apt install ffmpeg python3 python3-pip git cmake

# Install whisper.cpp
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp
cmake -B build
cmake --build build -j --config Release

# Download whisper model
bash ./models/download-ggml-model.sh medium
```

### Python Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration
```bash
# Set environment variables
export OLLAMA_API_KEY="1728cbe73f944db7afa1a3c8f52d2f41.GzEVZ8ADdcDHwIxdbvKnqbXy"

# Create necessary directories
mkdir -p temp notes models
```

### Run the Application
```bash
# Initialize database
python init_db.py

# Start Flask server
python app.py

# Access at http://localhost:5000
```

## Usage Examples

### Web Interface
1. Navigate to `http://localhost:5000`
2. Choose input method:
   - Paste YouTube URL, OR
   - Upload local video file
3. Click "Process"
4. Wait for transcription and note generation
5. View, edit, or download notes

### API Usage
```bash
# Process YouTube video
curl -X POST http://localhost:5000/process \
  -F "source=https://youtube.com/watch?v=xyz123"

# Process local file
curl -X POST http://localhost:5000/process \
  -F "source=@/path/to/video.mp4"

# Get notes
curl http://localhost:5000/notes/1

# Download notes
curl http://localhost:5000/download/1 -o notes.md
```

## Next Steps

1. Set up development environment
2. Test video/audio processing pipeline
3. Integrate Ollama API for note generation
4. Build basic web interface
5. Test with sample videos
6. Iterate on note quality and formatting
7. Add progress tracking
8. Deploy to production server

## Resources

- [whisper.cpp](https://github.com/ggerganov/whisper.cpp) - Audio transcription
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube downloader
- [Ollama](https://ollama.com) - AI model API
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [FFmpeg](https://ffmpeg.org/) - Media processing
