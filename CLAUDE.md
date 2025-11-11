start working on this we want to create web app where can can give upload video or youtube link and get ai enhanced notes using ollama
ollama api key: 1728cbe73f944db7afa1a3c8f52d2f41.GzEVZ8ADdcDHwIxdbvKnqbXy
First, install Ollama’s Python library

Copy
pip install ollama
Then make a request

Copy
import os
from ollama import Client

client = Client(
    host="https://ollama.com",
    headers={'Authorization': 'Bearer ' + os.environ.get('OLLAMA_API_KEY')}
)

messages = [
  {
    'role': 'user',
    'content': 'Why is the sky blue?',
  },
]

for part in client.chat('gpt-oss:120b', messages=messages, stream=True):
  print(part['message']['content'], end='', flush=True)


# BJJ Instructional Video → Notes System

## Overview
System to automatically convert long-form BJJ instructional videos (local files or YouTube) into structured, searchable notes with technique breakdowns and linking between related techniques.

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
  - Extract structured technique data
  - Identify positions, transitions, key details
  ↓
Knowledge Graph Storage (SQLite/Postgres)
  ↓
Note Generator (Markdown with bidirectional links)
  ↓
Web UI (Flask) - Browse, search, track progress
```

## Technology Stack

### Core Components
- **whisper.cpp**: Audio transcription with timestamps
  - Model: `medium` or `large` for BJJ terminology accuracy
  - Flag: `--word-timestamps` for video linking
- **yt-dlp**: YouTube video/audio download
- **ffmpeg**: Audio extraction from local videos
- **Ollama/Azure OpenAI**: Structured data extraction
- **Flask**: Web interface
- **SQLite/Postgres**: Technique database
- **Python**: Orchestration layer

### Libraries Needed
```python
# requirements.txt
yt-dlp
openai  # for Azure OpenAI
requests  # for Ollama API
flask
sqlite3  # built-in
markdown
```

## Implementation Components

### 1. Video Source Handler
```python
import yt_dlp
import os

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
    import subprocess
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
    # Split by sentences/paragraphs while preserving timestamps
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

### 3. AI Processing
```python
def extract_techniques(transcription_text, metadata, ai_model='ollama'):
    """
    Extract structured technique data using AI
    """
    prompt = f"""
You are analyzing a BJJ instructional video transcript.

Video Title: {metadata['title']}
Instructor: {metadata.get('channel', 'Unknown')}

Extract all techniques mentioned with the following structure:

For each technique, provide:
1. Technique name and variations
2. Starting position (mount, guard, side control, etc.)
3. Step-by-step breakdown (numbered steps)
4. Key details and common mistakes
5. Transitions/connections to other techniques
6. Timestamps where technique is discussed

Output as JSON array of techniques.

Transcript:
{transcription_text}

JSON Output:
"""

    if ai_model == 'ollama':
        return call_ollama(prompt)
    else:
        return call_azure_openai(prompt)

def call_ollama(prompt, model='llama3.1'):
    """Call local Ollama instance"""
    import requests
    response = requests.post('http://localhost:11434/api/generate', json={
        'model': model,
        'prompt': prompt,
        'stream': False,
        'format': 'json'
    })
    return response.json()['response']

def call_azure_openai(prompt):
    """Call Azure OpenAI"""
    from openai import AzureOpenAI
    client = AzureOpenAI(
        api_key=os.getenv('AZURE_OPENAI_KEY'),
        api_version='2024-02-15-preview',
        azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT')
    )
    
    response = client.chat.completions.create(
        model='gpt-4',
        messages=[{'role': 'user', 'content': prompt}],
        response_format={'type': 'json_object'}
    )
    return response.choices[0].message.content
```

### 4. Database Schema
```sql
-- techniques.sql

CREATE TABLE videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_url TEXT,
    title TEXT NOT NULL,
    instructor TEXT,
    duration INTEGER,
    upload_date DATE,
    processed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE techniques (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id INTEGER,
    name TEXT NOT NULL,
    starting_position TEXT,
    gi_or_nogi TEXT,
    description TEXT,
    steps TEXT, -- JSON array
    key_details TEXT,
    timestamps TEXT, -- JSON array of timestamp ranges
    FOREIGN KEY (video_id) REFERENCES videos(id)
);

CREATE TABLE positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL -- mount, guard, side control, etc.
);

CREATE TABLE technique_positions (
    technique_id INTEGER,
    position_id INTEGER,
    relationship TEXT, -- 'starts_from', 'ends_in', 'transitions_through'
    FOREIGN KEY (technique_id) REFERENCES techniques(id),
    FOREIGN KEY (position_id) REFERENCES positions(id)
);

CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL -- submission, sweep, escape, pass, etc.
);

CREATE TABLE technique_tags (
    technique_id INTEGER,
    tag_id INTEGER,
    FOREIGN KEY (technique_id) REFERENCES techniques(id),
    FOREIGN KEY (tag_id) REFERENCES tags(id)
);

CREATE TABLE technique_links (
    from_technique_id INTEGER,
    to_technique_id INTEGER,
    relationship TEXT, -- 'leads_to', 'counters', 'alternative_to'
    FOREIGN KEY (from_technique_id) REFERENCES techniques(id),
    FOREIGN KEY (to_technique_id) REFERENCES techniques(id)
);

CREATE TABLE user_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    technique_id INTEGER,
    date_drilled DATE,
    notes TEXT,
    proficiency INTEGER, -- 1-5 rating
    FOREIGN KEY (technique_id) REFERENCES techniques(id)
);

-- Indexes for fast lookups
CREATE INDEX idx_techniques_position ON techniques(starting_position);
CREATE INDEX idx_techniques_video ON techniques(video_id);
CREATE INDEX idx_links_from ON technique_links(from_technique_id);
CREATE INDEX idx_links_to ON technique_links(to_technique_id);
```

### 5. Note Generation
```python
def generate_markdown_note(technique_data, video_metadata):
    """
    Generate markdown note with links and structure
    """
    note = f"""# {technique_data['name']}

**Source**: [{video_metadata['title']}]({video_metadata['url']})
**Instructor**: {video_metadata['channel']}
**Position**: {technique_data['starting_position']}
**Tags**: {', '.join(technique_data.get('tags', []))}

---

## Overview
{technique_data['description']}

## Step-by-Step

"""
    
    for i, step in enumerate(technique_data['steps'], 1):
        timestamp = step.get('timestamp', '')
        timestamp_link = f"[{timestamp}]({video_metadata['url']}&t={convert_to_seconds(timestamp)}s)" if timestamp else ""
        note += f"{i}. {step['instruction']} {timestamp_link}\n"
    
    note += f"""

## Key Details
{technique_data['key_details']}

## Common Mistakes
{technique_data.get('common_mistakes', 'N/A')}

## Transitions
"""
    
    for transition in technique_data.get('transitions', []):
        note += f"- [[{transition}]]\n"
    
    note += """

## Related Techniques
"""
    
    for related in technique_data.get('related_techniques', []):
        note += f"- [[{related}]]\n"
    
    return note

def convert_to_seconds(timestamp):
    """Convert MM:SS or HH:MM:SS to seconds"""
    parts = timestamp.split(':')
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    elif len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    return 0
```

### 6. Flask Web Interface
```python
from flask import Flask, render_template, request, jsonify
import sqlite3

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_video_endpoint():
    """Handle video processing request"""
    source = request.form['source']  # URL or file path
    
    try:
        # 1. Download/extract audio
        metadata = process_video(source)
        
        # 2. Transcribe
        transcription = transcribe_with_whisper(metadata['audio_path'])
        
        # 3. Extract techniques
        techniques = extract_techniques(transcription, metadata)
        
        # 4. Store in database
        video_id = store_video(metadata)
        for tech in techniques:
            store_technique(tech, video_id)
        
        # 5. Generate notes
        notes = [generate_markdown_note(tech, metadata) for tech in techniques]
        
        return jsonify({'success': True, 'techniques': len(techniques)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/search')
def search():
    """Search techniques by position, name, tag"""
    query = request.args.get('q', '')
    position = request.args.get('position', '')
    tag = request.args.get('tag', '')
    
    conn = sqlite3.connect('bjj_notes.db')
    cursor = conn.cursor()
    
    # Build dynamic query
    sql = "SELECT * FROM techniques WHERE 1=1"
    params = []
    
    if query:
        sql += " AND name LIKE ?"
        params.append(f'%{query}%')
    if position:
        sql += " AND starting_position = ?"
        params.append(position)
    
    cursor.execute(sql, params)
    results = cursor.fetchall()
    conn.close()
    
    return jsonify(results)

@app.route('/technique/<int:technique_id>')
def view_technique(technique_id):
    """View individual technique note"""
    conn = sqlite3.connect('bjj_notes.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM techniques WHERE id = ?", (technique_id,))
    technique = cursor.fetchone()
    conn.close()
    
    return render_template('technique.html', technique=technique)

if __name__ == '__main__':
    app.run(debug=True)
```

## Project Structure
```
bjj-notes/
├── app.py                 # Flask application
├── requirements.txt       # Python dependencies
├── config.py             # Configuration (API keys, paths)
├── models/               # Whisper models
│   └── ggml-medium.bin
├── processors/
│   ├── video_handler.py  # YouTube/local video processing
│   ├── transcriber.py    # Whisper integration
│   ├── ai_extractor.py   # AI technique extraction
│   └── note_generator.py # Markdown generation
├── database/
│   ├── schema.sql        # Database schema
│   └── db_manager.py     # Database operations
├── static/
│   ├── css/
│   └── js/
├── templates/
│   ├── index.html        # Main upload interface
│   ├── search.html       # Search interface
│   └── technique.html    # Individual technique view
├── temp/                 # Temporary audio files
└── notes/                # Generated markdown notes
```

## Features to Implement

### Phase 1: Core Functionality
- [x] Video download (YouTube + local)
- [x] Audio transcription with timestamps
- [x] AI technique extraction
- [x] Basic database storage
- [x] Markdown note generation

### Phase 2: Linking System
- [ ] Automatic technique linking by position
- [ ] Transition mapping
- [ ] Bidirectional links (Zettelkasten style)
- [ ] Tag system (submission, sweep, escape, pass)
- [ ] Position taxonomy (mount, guard, back, etc.)

### Phase 3: Enhancement
- [ ] Video chapter detection and parsing
- [ ] Instructor recognition/tagging
- [ ] Gi vs No-Gi classification
- [ ] Belt level recommendations
- [ ] Progress tracking (techniques drilled)
- [ ] Spaced repetition reminders

### Phase 4: Advanced Features
- [ ] Technique clustering (related moves)
- [ ] Search by scenario ("bottom side control escapes")
- [ ] Video timestamp jump (click to watch)
- [ ] Export to Anki flashcards
- [ ] Mobile app for drilling notes
- [ ] Integration with existing Zettelkasten

## Configuration Example
```python
# config.py

import os

class Config:
    # Paths
    TEMP_DIR = './temp'
    NOTES_DIR = './notes'
    MODELS_DIR = './models'
    DATABASE_PATH = './bjj_notes.db'
    
    # Whisper
    WHISPER_MODEL = 'medium'  # or 'large' for better accuracy
    WHISPER_PATH = './whisper.cpp/main'
    
    # AI Model
    AI_PROVIDER = 'ollama'  # or 'azure'
    OLLAMA_URL = 'http://localhost:11434'
    OLLAMA_MODEL = 'llama3.1'
    
    # Azure OpenAI (if using)
    AZURE_OPENAI_KEY = os.getenv('AZURE_OPENAI_KEY')
    AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-prod')
    DEBUG = True
```

## Usage Examples

### Command Line
```bash
# Process YouTube video
python cli.py process https://youtube.com/watch?v=xyz123

# Process local video
python cli.py process /path/to/video.mp4

# Search techniques
python cli.py search "armbar from mount"

# Search by position
python cli.py search --position "closed guard"
```

### Web Interface
```
1. Navigate to http://localhost:5000
2. Paste YouTube URL or upload video file
3. Click "Process"
4. View extracted techniques with timestamps
5. Browse linked techniques by position/transition
```

## Next Steps

1. Set up whisper.cpp and download models
2. Test yt-dlp with sample BJJ video
3. Build basic transcription pipeline
4. Experiment with AI prompts for technique extraction
5. Design database schema and create tables
6. Build Flask UI for uploading/viewing
7. Implement linking algorithm
8. Add search and filtering

## Resources

- whisper.cpp: https://github.com/ggerganov/whisper.cpp
- yt-dlp: https://github.com/yt-dlp/yt-dlp
- Ollama: https://ollama.ai
- Flask: https://flask.palletsprojects.com/

## Notes

- Consider running on homelab servers (Nextcloud integration?)
- Could integrate with existing Zettelkasten note system
- Privacy: all processing can be done locally with Ollama
- Cost: Azure OpenAI may be needed for complex extraction
- Consider batch processing for multiple videos overnight

Using whisper.cpp
# How to Use whisper.cpp

**whisper.cpp** is a C/C++ implementation of OpenAI's Whisper automatic speech recognition model for converting audio to text.

## Quick Start

### 1. Clone and Navigate to the Repository

```bash
git clone https://github.com/ggml-org/whisper.cpp.git
cd whisper.cpp
```

### 2. Download a Model

Download one of the Whisper models (e.g., `base.en`):

```bash
sh ./models/download-ggml-model.sh base.en
```

### 3. Build the Project

```bash
cmake -B build
cmake --build build -j --config Release
```

### 4. Transcribe Audio

```bash
./build/bin/whisper-cli -f samples/jfk.wav
```

## Audio Format Requirements

**Important:** whisper-cli currently only works with 16-bit WAV files.

### Convert Audio Files

Use ffmpeg to convert your audio to the correct format:

```bash
ffmpeg -i input.mp3 -ar 16000 -ac 1 -c:a pcm_s16le output.wav
```

Parameters:
- `-ar 16000`: Sample rate of 16kHz
- `-ac 1`: Mono audio (1 channel)
- `-c:a pcm_s16le`: 16-bit PCM encoding

## Available Models

| Model     | Disk Size | Memory Usage |
|-----------|-----------|--------------|
| tiny      | 75 MiB    | ~273 MB      |
| base      | 142 MiB   | ~388 MB      |
| small     | 466 MiB   | ~852 MB      |
| medium    | 1.5 GiB   | ~2.1 GB      |
| large     | 2.9 GiB   | ~3.9 GB      |

### Download Models

```bash
# English-only models (faster, smaller)
make tiny.en
make base.en
make small.en
make medium.en

# Multilingual models
make tiny
make base
make small
make medium
make large-v1
make large-v2
make large-v3
make large-v3-turbo
```

## Common Use Cases

### Basic Transcription

```bash
./build/bin/whisper-cli -m models/ggml-base.en.bin -f samples/jfk.wav
```

### Word-Level Timestamps

```bash
./build/bin/whisper-cli -m models/ggml-base.en.bin -f samples/jfk.wav -ml 1
```

### Transcription with Color-Coded Confidence

```bash
./build/bin/whisper-cli -m models/ggml-base.en.bin -f samples/jfk.wav --print-colors
```

### Real-Time Microphone Transcription

First, install SDL2, then:

```bash
cmake -B build -DWHISPER_SDL2=ON
cmake --build build -j --config Release
./build/bin/whisper-stream -m ./models/ggml-base.en.bin -t 8 --step 500 --length 5000
```

### Voice Activity Detection (VAD)

Download a VAD model:

```bash
./models/download-vad-model.sh silero-v5.1.2
```

Use with whisper:

```bash
./build/bin/whisper-cli \
  --file ./samples/jfk.wav \
  --model ./models/ggml-base.en.bin \
  --vad \
  --vad-model ./models/ggml-silero-v5.1.2.bin
```

## GPU Acceleration

### NVIDIA GPU (CUDA)

```bash
cmake -B build -DGGML_CUDA=1
cmake --build build -j --config Release
```

For newer RTX 5000 series:

```bash
cmake -B build -DGGML_CUDA=1 -DCMAKE_CUDA_ARCHITECTURES="86"
cmake --build build -j --config Release
```

### Apple Silicon (Metal/Core ML)

Install Python dependencies:

```bash
pip install ane_transformers openai-whisper coremltools
```

Generate Core ML model:

```bash
./models/generate-coreml-model.sh base.en
```

Build with Core ML support:

```bash
cmake -B build -DWHISPER_COREML=1
cmake --build build -j --config Release
```

### Vulkan (Cross-platform GPU)

```bash
cmake -B build -DGGML_VULKAN=1
cmake --build build -j --config Release
```

### Intel GPU / CPU (OpenVINO)

Setup Python environment:

```bash
cd models
python3 -m venv openvino_conv_env
source openvino_conv_env/bin/activate
pip install -r requirements-openvino.txt
```

Generate OpenVINO model:

```bash
python convert-whisper-to-openvino.py --model base.en
```

Build with OpenVINO:

```bash
cmake -B build -DWHISPER_OPENVINO=1
cmake --build build -j --config Release
```

## Advanced Features

### Model Quantization

Reduce model size and memory usage:

```bash
# Build quantize tool
cmake -B build
cmake --build build -j --config Release

# Quantize model
./build/bin/quantize models/ggml-base.en.bin models/ggml-base.en-q5_0.bin q5_0

# Use quantized model
./build/bin/whisper-cli -m models/ggml-base.en-q5_0.bin ./samples/jfk.wav
```

### Speaker Segmentation (tinydiarize)

```bash
# Download compatible model
./models/download-ggml-model.sh small.en-tdrz

# Run with speaker detection
./build/bin/whisper-cli -f ./samples/a13.wav -m ./models/ggml-small.en-tdrz.bin -tdrz
```

### FFmpeg Support (More Audio Formats)

Linux:

```bash
# Install dependencies
sudo apt install libavcodec-dev libavformat-dev libavutil-dev  # Debian/Ubuntu
sudo dnf install libavcodec-free-devel libavformat-free-devel libavutil-free-devel  # RHEL/Fedora

# Build with FFmpeg
cmake -B build -DWHISPER_FFMPEG=yes
cmake --build build -j --config Release

# Now you can use Opus, AAC, etc.
./build/bin/whisper-cli --model models/ggml-base.en.bin --file audio.opus
```

## Docker Usage

### Pull and Run

```bash
# Download model
docker run -it --rm \
  -v path/to/models:/models \
  ghcr.io/ggml-org/whisper.cpp:main "./models/download-ggml-model.sh base /models"

# Transcribe audio
docker run -it --rm \
  -v path/to/models:/models \
  -v path/to/audios:/audios \
  ghcr.io/ggml-org/whisper.cpp:main "whisper-cli -m /models/ggml-base.bin -f /audios/jfk.wav"
```

### With CUDA Support

```bash
docker run -it --rm --gpus all \
  -v path/to/models:/models \
  -v path/to/audios:/audios \
  ghcr.io/ggml-org/whisper.cpp:main-cuda "whisper-cli -m /models/ggml-base.bin -f /audios/jfk.wav"
```

## Command-Line Options

Get full help:

```bash
./build/bin/whisper-cli -h
```

Common options:
- `-f FILE`: Input audio file
- `-m MODEL`: Model file path
- `-t N`: Number of threads (default: 4)
- `-l LANG`: Language code (e.g., "en", "es", "fr")
- `-ml N`: Maximum segment length in characters
- `--print-colors`: Color-code transcription by confidence
- `--vad`: Enable Voice Activity Detection

## Troubleshooting

### Audio File Not Working

Ensure your audio is in the correct format:

```bash
ffmpeg -i input.mp3 -ar 16000 -ac 1 -c:a pcm_s16le output.wav
```

### Out of Memory

Try a smaller model (e.g., `tiny` or `base`) or use quantization.

### Slow Performance

- Use GPU acceleration (CUDA, Metal, Vulkan)
- Use a smaller model
- Enable VAD to skip non-speech segments
- Increase thread count with `-t` flag

## Additional Resources

- **Examples:** See the `examples/` folder for iOS, Android, server, and WebAssembly implementations
- **Bindings:** Available for Python, JavaScript, Go, Java, Ruby, Rust, .NET, and more
- **Discussions:** https://github.com/ggml-org/whisper.cpp/discussions
- **FAQ:** https://github.com/ggml-org/whisper.cpp/discussions/126

# Audio to Markdown Notes - Whisper.cpp Guide

## Overview

Ref How to: [[howto]]

Convert audio recordings (lectures, meetings, interviews, voice memos) into well-formatted, accurate Markdown notes using **Whisper.cpp** for local transcription and AI for formatting.

**Why Whisper.cpp?**
- ✅ Completely free and private (no cloud needed for transcription)
- ✅ Fast (2-10x faster than Python Whisper)
- ✅ Runs on laptop, phone (Termux), or as web service
- ✅ Low resource usage (works on CPU, GPU optional)
- ✅ Cross-platform (Linux, macOS, Windows, Android)

## The Two-Step Process

### Step 1: Audio → Text (Transcription with Whisper.cpp)
Extract accurate text from audio using optimized local Whisper models

### Step 2: Text → Formatted Markdown (AI Formatting)
Transform raw transcript into structured, readable notes using Claude/GPT

## Whisper.cpp: Core Transcription Tool

**What is Whisper.cpp?**
- C++ port of OpenAI Whisper (much faster than Python version)
- Runs locally on any device
- Same accuracy as original Whisper
- Optimized for CPU (GPU support optional)

**Performance:**
- **Laptop**: 1-3x real-time (20-60 min for 1 hour audio)
- **Desktop with GPU**: 5-10x real-time (6-12 min for 1 hour audio)
- **Phone (Termux)**: 0.5x real-time (2 hours for 1 hour audio with tiny model)

## Whisper.cpp Installation

### On Laptop (Linux/macOS/Windows)

```bash
# Clone repository
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp

# Build
make

# Download models (choose one or multiple)
bash ./models/download-ggml-model.sh tiny     # 75 MB - fastest
bash ./models/download-ggml-model.sh base     # 142 MB - good balance
bash ./models/download-ggml-model.sh small    # 466 MB - better accuracy
bash ./models/download-ggml-model.sh medium   # 1.5 GB - excellent
```

**Test it:**
```bash
# Basic transcription
./main -m models/ggml-base.bin -f audio.wav

# Output to text file
./main -m models/ggml-base.bin -f audio.wav -otxt

# With language hint (faster, more accurate)
./main -m models/ggml-base.bin -f audio.wav -l en -otxt
```

### On Phone (Android with Termux)

```bash
# Install Termux from F-Droid (not Play Store)
# Open Termux and run:

pkg update && pkg upgrade
pkg install git clang make

# Clone and build
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp
make

# Download tiny or base model (larger models too slow on phone)
bash ./models/download-ggml-model.sh tiny

# Transcribe (use recordings from phone)
./main -m models/ggml-tiny.bin -f ~/storage/shared/recording.wav -otxt
```

**Pro tip for phone:** Set up Termux storage access first
```bash
termux-setup-storage
# Then access phone files at ~/storage/shared/
```

### On Servers (frodo/legolas/gandalf)

Same as laptop installation. Recommended model for 8GB RAM: `small` or `medium`

## Implementation Methods

### Method 1: Laptop - Simple CLI Script (Recommended)

**Full automation: Drop audio → Get markdown notes**

```bash
#!/bin/bash
# audio2note.sh - Whisper.cpp + Claude API

AUDIO_FILE="$1"
BASE_NAME=$(basename "$AUDIO_FILE" | sed 's/\.[^.]*$//')
WHISPER_MODEL="${WHISPER_MODEL:-$HOME/whisper.cpp/models/ggml-base.bin}"

# Step 1: Transcribe with whisper.cpp
echo "Transcribing with whisper.cpp..."
~/whisper.cpp/main \
  -m "$WHISPER_MODEL" \
  -f "$AUDIO_FILE" \
  -l en \
  -otxt \
  -of "/tmp/${BASE_NAME}"

TRANSCRIPT=$(cat "/tmp/${BASE_NAME}.txt")

# Step 2: Format with Claude API
echo "Formatting notes with AI..."
FORMATTED_NOTES=$(curl -s https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d "{
    \"model\": \"claude-sonnet-4-20250514\",
    \"max_tokens\": 4096,
    \"messages\": [{
      \"role\": \"user\",
      \"content\": \"Convert this transcript into well-structured markdown notes:\n\n- Use clear headings (##, ###)\n- Organize into logical sections\n- Use bullet points for lists\n- Bold important terms\n- Add a 'Key Takeaways' section\n- Fix transcription errors\n\nTranscript:\n$TRANSCRIPT\"
    }]
  }" | jq -r '.content[0].text')

# Save markdown
echo "$FORMATTED_NOTES" > "${BASE_NAME}.md"
echo "✓ Notes saved to: ${BASE_NAME}.md"

# Cleanup
rm "/tmp/${BASE_NAME}.txt"
```

**Setup:**
```bash
# Save script
curl -o ~/bin/audio2note https://gist.example.com/audio2note.sh
chmod +x ~/bin/audio2note

# Set API key
echo 'export ANTHROPIC_API_KEY="your-key-here"' >> ~/.bashrc
source ~/.bashrc

# Optional: Set preferred model
echo 'export WHISPER_MODEL="$HOME/whisper.cpp/models/ggml-small.bin"' >> ~/.bashrc
```

**Usage:**
```bash
audio2note lecture.mp3
audio2note meeting.wav
audio2note ~/Downloads/interview.m4a
```

### Method 2: Phone - Termux Automation

**Record on phone → Auto-transcribe → Format later**

```bash
#!/data/data/com.termux/files/usr/bin/bash
# ~/bin/phone-audio2note

AUDIO_FILE="$1"
BASE_NAME=$(basename "$AUDIO_FILE" .wav")
WHISPER_DIR="$HOME/whisper.cpp"

# Transcribe with tiny model (faster on phone)
echo "Transcribing..."
cd "$WHISPER_DIR"
./main -m models/ggml-tiny.bin -f "$AUDIO_FILE" -l en -otxt -of "/tmp/${BASE_NAME}"

# Save transcript to accessible location
cp "/tmp/${BASE_NAME}.txt" ~/storage/shared/transcripts/

echo "Transcript saved to: ~/storage/shared/transcripts/${BASE_NAME}.txt"
echo "Format it later by pasting into Claude.ai"
```

**Workflow:**
1. Record audio with phone recorder
2. Run: `phone-audio2note ~/storage/shared/recording.wav`
3. Open transcript file on phone
4. Copy-paste to Claude.ai mobile app
5. Ask: "Format this as markdown notes"
6. Save result to Notes app

**Advanced:** Use Termux-API for notifications
```bash
pkg install termux-api
# Add to script:
termux-notification -t "Transcription Done" -c "Ready to format"
```

### Method 3: Web App (Self-Hosted on frodo)

**Create a simple web interface for your network**

**Backend (Flask + Whisper.cpp):**
```python
#!/usr/bin/env python3
# ~/whisper-webapp/app.py

from flask import Flask, request, render_template, jsonify
import subprocess
import os
import requests

app = Flask(__name__)
WHISPER_BIN = "/home/parteek/whisper.cpp/main"
WHISPER_MODEL = "/home/parteek/whisper.cpp/models/ggml-base.bin"
UPLOAD_FOLDER = "/tmp/whisper-uploads"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'audio' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['audio']
    filename = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filename)

    # Transcribe with whisper.cpp
    base_name = os.path.splitext(filename)[0]
    subprocess.run([
        WHISPER_BIN,
        '-m', WHISPER_MODEL,
        '-f', filename,
        '-l', 'en',
        '-otxt',
        '-of', base_name
    ])

    # Read transcript
    with open(f"{base_name}.txt", 'r') as f:
        transcript = f.read()

    return jsonify({'transcript': transcript})

@app.route('/format', methods=['POST'])
def format_notes():
    transcript = request.json.get('transcript', '')

    # Format with Claude
    response = requests.post(
        'https://api.anthropic.com/v1/messages',
        headers={
            'x-api-key': ANTHROPIC_API_KEY,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json'
        },
        json={
            'model': 'claude-sonnet-4-20250514',
            'max_tokens': 4096,
            'messages': [{
                'role': 'user',
                'content': f"""Convert this transcript into well-structured markdown notes:

- Use clear headings (##, ###)
- Organize into logical sections
- Use bullet points for lists
- Bold important terms
- Add a "Key Takeaways" section
- Fix any transcription errors

Transcript:
{transcript}"""
            }]
        }
    )

    notes = response.json()['content'][0]['text']
    return jsonify({'notes': notes})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

**Frontend (templates/index.html):**
```html
<!DOCTYPE html>
<html>
<head>
    <title>Audio2Note</title>
    <style>
        body { font-family: sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
        textarea { width: 100%; height: 300px; margin: 10px 0; }
        button { padding: 10px 20px; margin: 5px; cursor: pointer; }
        .status { color: #666; font-style: italic; }
    </style>
</head>
<body>
    <h1>Audio to Markdown Notes</h1>

    <input type="file" id="audioFile" accept="audio/*">
    <button onclick="transcribe()">1. Transcribe</button>

    <h3>Transcript:</h3>
    <textarea id="transcript" placeholder="Transcript will appear here..."></textarea>

    <button onclick="formatNotes()">2. Format to Markdown</button>

    <h3>Formatted Notes:</h3>
    <textarea id="notes" placeholder="Formatted notes will appear here..."></textarea>

    <button onclick="downloadNotes()">Download .md</button>

    <p class="status" id="status"></p>

    <script>
        async function transcribe() {
            const fileInput = document.getElementById('audioFile');
            const file = fileInput.files[0];
            if (!file) { alert('Select an audio file first'); return; }

            document.getElementById('status').textContent = 'Transcribing...';

            const formData = new FormData();
            formData.append('audio', file);

            const response = await fetch('/transcribe', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            document.getElementById('transcript').value = data.transcript;
            document.getElementById('status').textContent = 'Transcription complete!';
        }

        async function formatNotes() {
            const transcript = document.getElementById('transcript').value;
            if (!transcript) { alert('Transcribe audio first'); return; }

            document.getElementById('status').textContent = 'Formatting with AI...';

            const response = await fetch('/format', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({transcript})
            });

            const data = await response.json();
            document.getElementById('notes').value = data.notes;
            document.getElementById('status').textContent = 'Done!';
        }

        function downloadNotes() {
            const notes = document.getElementById('notes').value;
            const blob = new Blob([notes], {type: 'text/markdown'});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'notes.md';
            a.click();
        }
    </script>
</body>
</html>
```

**Setup on frodo:**
```bash
# Install dependencies
pip3 install flask requests

# Set API key
export ANTHROPIC_API_KEY="your-key-here"

# Run webapp
cd ~/whisper-webapp
python3 app.py

# Access from any device on network: http://frodo:5000
```

**Make it a service (runs on boot):**
```bash
# Create systemd service
sudo tee /etc/systemd/system/audio2note.service <<EOF
[Unit]
Description=Audio2Note Web Service
After=network.target

[Service]
User=parteek
WorkingDirectory=/home/parteek/whisper-webapp
Environment="ANTHROPIC_API_KEY=your-key-here"
ExecStart=/usr/bin/python3 app.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable audio2note
sudo systemctl start audio2note
```

## Advanced AI Formatting Prompts

### Basic Formatting
```
Convert this transcript into markdown notes with clear structure and headings.
```

### Academic Lecture
```
Convert this lecture transcript into comprehensive markdown notes:
- Main concepts as ## headings
- Supporting details as bullet points
- Important definitions in bold
- Examples in blockquotes
- Add a summary section at the end
```

### Meeting Notes
```
Convert this meeting transcript into actionable notes:
- Decisions made
- Action items with owners
- Key discussion points
- Next steps
- Follow-up questions
Use clear markdown formatting.
```

### Interview/Podcast
```
Format this interview transcript:
- Identify speakers (Interviewer/Guest)
- Organize by topics discussed
- Highlight key insights
- Pull out memorable quotes
- Add timestamps if available
```

### Voice Memo/Brainstorm
```
Organize these voice notes into structured markdown:
- Group related ideas
- Separate actionable items from general thoughts
- Highlight innovative concepts
- Suggest logical flow/order
```

## Complete Example Workflow

### Example: Lecture Recording

**Input**: `physics_lecture.mp3` (45 minutes)

**Step 1: Transcribe**
```bash
# Using OpenAI Whisper API
curl https://api.openai.com/v1/audio/transcriptions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -F file="@physics_lecture.mp3" \
  -F model="whisper-1" \
  > transcript.txt
```

**Step 2: Format with AI**
```bash
# Using Claude
claude_prompt="Convert this physics lecture transcript into comprehensive markdown notes. Include equations in LaTeX format where applicable."

# Send to Claude API with transcript
# (see scripts above)
```

**Output**: `physics_lecture.md`
```markdown
# Physics Lecture - Quantum Mechanics Basics

## Introduction to Wave-Particle Duality

- Light exhibits both wave and particle properties
- Classical physics cannot explain photoelectric effect
- Einstein's photon theory: $E = h\nu$

### Key Experiments

**Double-slit experiment**
- Demonstrates wave interference
- Individual photons still create interference pattern
- Observation collapses wave function

### Important Equations

The Schrödinger equation:
$$i\hbar\frac{\partial}{\partial t}\Psi = \hat{H}\Psi$$

## Heisenberg Uncertainty Principle

Cannot simultaneously know:
- Exact position AND momentum
- Equation: $\Delta x \cdot \Delta p \geq \frac{\hbar}{2}$

## Key Takeaways

1. Quantum mechanics fundamentally probabilistic
2. Measurement affects the system
3. Wave function describes probability distribution
4. Classical intuition fails at quantum scale

## Questions for Review

- What is the significance of Planck's constant?
- How does observation affect quantum systems?
- Explain wave function collapse
```

## Cost Analysis (Whisper.cpp Focus)

### For 1 Hour of Audio

| Method | Transcription | Formatting | Total | Notes |
|--------|---------------|------------|-------|-------|
| **Whisper.cpp + Claude API** | **$0.00** | **$0.03** | **$0.03** | **Recommended** |
| Whisper.cpp + Claude free tier | $0.00 | $0.00 | **$0.00** | Best for < 5hrs/month |
| Whisper.cpp + ChatGPT | $0.00 | $0.02 | **$0.02** | Alternative |
| 100% Free (whisper.cpp + manual) | $0.00 | $0.00 | **$0.00** | Copy to Claude.ai |

**Bottom line:** Transcription is FREE with Whisper.cpp. Only pay for AI formatting if you want automation.

### Budget Recommendations

- **Low volume** (< 5 hrs/month): Whisper.cpp + Claude.ai free tier = $0
- **Medium volume** (5-50 hrs/month): Whisper.cpp + Claude API = ~$1.50-5/month
- **High volume** (> 50 hrs/month): Same! Still cheap at ~$10/month
- **Privacy-focused**: 100% local (Whisper.cpp + local LLM like Llama) = $0

## Hardware Requirements (Whisper.cpp)

### Device Compatibility

| Device | Model | RAM | Time (1hr audio) | Recommended Use |
|--------|-------|-----|------------------|-----------------|
| **Phone** (Termux) | tiny | 2GB | ~2 hours | Quick voice memos |
| **Phone** (Termux) | base | 4GB | ~3 hours | Longer recordings |
| **Laptop** (CPU) | base | 4GB | ~30-60 min | General use |
| **Laptop** (CPU) | small | 4GB | ~45-90 min | Better accuracy |
| **Laptop** (CPU) | medium | 8GB | ~90-180 min | Technical content |
| **Server** (frodo 8GB) | small | 4GB | ~30-60 min | Web service |
| **Server** (frodo 8GB) | medium | 8GB | ~60-120 min | Best quality |
| **Desktop** (GPU) | large | 10GB | ~6-12 min | Production |

### Whisper.cpp Model Sizes

| Model | Size | RAM Usage | Accuracy | Best For |
|-------|------|-----------|----------|----------|
| **tiny** | 75 MB | ~1 GB | Fair (85%) | Phone, quick notes |
| **base** | 142 MB | ~1 GB | Good (90%) | Laptop default |
| **small** | 466 MB | ~2 GB | Very good (94%) | Best balance |
| **medium** | 1.5 GB | ~5 GB | Excellent (97%) | Technical/medical |
| **large** | 2.9 GB | ~10 GB | Best (98%) | Professional use |

**Recommendations:**
- **Phone**: Start with `tiny`, upgrade to `base` if you have 4GB+ RAM
- **Laptop**: Use `base` or `small` for daily use
- **Server (frodo/legolas/gandalf)**: Use `small` or `medium`
- **Technical content**: Use at least `small`, preferably `medium`

## AI Formatting Options (100% Free!)

### Option 1: Claude.ai (Free Tier - Recommended)
- **Cost**: Free (with limits)
- **Quality**: Excellent
- **Limits**: ~30-50 messages/day
- **Best for**: Manual workflow (copy-paste transcript)

### Option 2: Ollama (Local AI - 100% Free)
- **Cost**: $0 (runs locally)
- **Quality**: Good (depends on model)
- **Limits**: None (unlimited)
- **Best for**: Automation + privacy

**Setup Ollama on laptop/server:**
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Download a model (choose one)
ollama pull llama3.2    # 3B params - fast, good quality
ollama pull llama3.1    # 8B params - better quality
ollama pull qwen2.5     # 7B params - excellent for formatting

# Test it
ollama run llama3.2 "Format this as markdown notes: Today we discussed..."
```

**Updated audio2note script with Ollama:**
```bash
#!/bin/bash
# audio2note-ollama.sh - 100% free & private

AUDIO_FILE="$1"
BASE_NAME=$(basename "$AUDIO_FILE" | sed 's/\.[^.]*$//')
WHISPER_MODEL="${WHISPER_MODEL:-$HOME/whisper.cpp/models/ggml-base.bin}"

# Step 1: Transcribe with whisper.cpp
echo "Transcribing with whisper.cpp..."
~/whisper.cpp/main -m "$WHISPER_MODEL" -f "$AUDIO_FILE" -l en -otxt -of "/tmp/${BASE_NAME}"
TRANSCRIPT=$(cat "/tmp/${BASE_NAME}.txt")

# Step 2: Format with Ollama (free, local)
echo "Formatting notes with Ollama..."
FORMATTED_NOTES=$(ollama run llama3.2 "Convert this transcript into well-structured markdown notes with headings, bullet points, key takeaways, and fix any errors:\n\n$TRANSCRIPT")

echo "$FORMATTED_NOTES" > "${BASE_NAME}.md"
echo "✓ Notes saved to: ${BASE_NAME}.md"
rm "/tmp/${BASE_NAME}.txt"
```

**No API key needed!** Completely free and private.

### Option 3: ChatGPT Free Tier
- **Cost**: Free (with limits)
- **Quality**: Excellent
- **Limits**: Limited messages
- **Best for**: Occasional use

### Cost Comparison

| Formatting Method | Cost/Hour | Setup | Privacy | Quality |
|-------------------|-----------|-------|---------|---------|
| **Ollama (local)** | **$0** | Medium | ✅ 100% | Good |
| **Claude.ai free** | **$0** | None | ⚠️ Cloud | Excellent |
| Claude API | $0.03 | Easy | ⚠️ Cloud | Excellent |
| ChatGPT free | $0 | None | ⚠️ Cloud | Excellent |
| GPT-4 API | $0.05 | Easy | ⚠️ Cloud | Excellent |

**Best combo for 100% free:**
- **Transcription**: Whisper.cpp (local, free)
- **Formatting**: Ollama (local, free) OR Claude.ai free tier (cloud)

## Improving Transcription Accuracy

### Pre-Processing Audio with Whisper.cpp

```bash
# Convert to optimal format (16kHz mono WAV)
ffmpeg -i input.mp3 -ar 16000 -ac 1 output.wav

# Reduce background noise
ffmpeg -i input.mp3 -af "highpass=f=200, lowpass=f=3000" cleaned.mp3

# Normalize volume
ffmpeg -i input.mp3 -af "loudnorm" normalized.mp3
```

### Whisper.cpp Tips

**Language specification (faster + more accurate):**
```bash
./main -m models/ggml-base.bin -f audio.wav -l en
```

**Initial prompt for context:**
```bash
./main -m models/ggml-base.bin -f audio.wav --prompt "This is a lecture about quantum physics"
```

**Best practices:**
- Better audio quality = better transcription
- Use at least `small` model for technical content
- Use `medium` for medical/legal terminology
- Specify language with `-l en` for 20-30% speedup

### Post-Processing

Let the AI fix transcription errors in the formatting step - both Claude and Ollama will automatically:
- Fix obvious transcription errors
- Correct technical terms
- Improve punctuation
- Structure content logically

## Integration with Your Setup

### Nextcloud Integration

```bash
# Watch Nextcloud folder for new audio files
inotifywait -m /path/to/nextcloud/Audio -e create |
while read path action file; do
    if [[ "$file" =~ \.(mp3|wav|m4a)$ ]]; then
        /usr/local/bin/audio2note "$path$file"
    fi
done
```

### Immich Integration

- Tag audio files in Immich
- Periodically export and process
- Store markdown notes back in Nextcloud

### Automated Workflow

```bash
# Cron job: Process any audio in ~/Audio/to_process/
# Save notes to ~/Notes/

*/15 * * * * /usr/local/bin/batch-audio2note.sh
```

## Quality Control Checklist

After generation, verify:

- [ ] Timestamps preserved (if needed)
- [ ] Technical terms spelled correctly
- [ ] Structure makes logical sense
- [ ] No missing sections
- [ ] Action items clearly marked
- [ ] Speaker attribution (if multi-person)
- [ ] Equations formatted properly

## Troubleshooting

### Common Issues

**Low accuracy transcription:**
- Use better audio source
- Pre-process audio (denoise)
- Use larger Whisper model
- Specify language explicitly

**AI formatting is poor:**
- Provide more specific prompt
- Include example format
- Use better model (Claude Opus, GPT-4)
- Break long transcripts into chunks

**Out of memory:**
- Use smaller Whisper model
- Process in chunks
- Close other applications
- Upgrade server RAM

**Slow processing:**
- Use faster Whisper model (tiny/base)
- Use Whisper.cpp instead of Python
- Use cloud API instead of local
- Add GPU to server

## Privacy Considerations

### Cloud APIs
- ✅ Fast and accurate
- ❌ Audio sent to third party
- ❌ Potential data retention

### Self-Hosted
- ✅ Complete privacy
- ✅ No data leaves your servers
- ❌ Requires setup and resources

### Hybrid Approach
- Transcribe locally (Whisper)
- Format with cloud AI (transcript only, not audio)
- Reasonable privacy with convenience

## Advanced Features

### Speaker Diarization

Identify who is speaking:

```python
# Using pyannote.audio
from pyannote.audio import Pipeline

pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization")
diarization = pipeline("audio.wav")

# Output: Speaker A: 0s-15s, Speaker B: 15s-32s, etc.
```

Then format with AI:
```
Format this transcript with speaker labels:
[0-15s] Speaker A: "Hello everyone..."
[15-32s] Speaker B: "Thanks for having me..."
```

### Timestamp Preservation

```bash
# Whisper with timestamps
whisper audio.mp3 --output_format srt

# Converts to:
# 1
# 00:00:00,000 --> 00:00:05,000
# This is the first segment
```

Then ask AI to preserve timestamps in markdown:
```markdown
## [00:00] Introduction
- [00:15] Topic overview
- [01:30] Main concept explained
```

### Multi-Language Support

```bash
# Auto-detect language
whisper audio.mp3 --task transcribe

# Translate to English
whisper audio.mp3 --task translate --language fr
```

### Custom Vocabulary

For technical terms, names, acronyms:

```python
# Initial prompt helps Whisper
result = model.transcribe(
    "audio.mp3",
    initial_prompt="This lecture discusses Kubernetes, PostgreSQL, and REST APIs."
)
```

## Quick Start Guide

### Beginner: Manual (100% Free)

1. **On Laptop**: Install Whisper.cpp (5 min)
2. **Transcribe**: `./main -m models/ggml-base.bin -f audio.mp3 -otxt`
3. **Format**: Copy transcript to Claude.ai, ask "Format as markdown notes"
4. **Save**: Copy result to `.md` file

**Time**: 10 min setup, 2 min per file
**Cost**: $0

### Intermediate: Automated + Free (Recommended)

1. **Install Whisper.cpp**: See installation section above
2. **Install Ollama**: `curl -fsSL https://ollama.com/install.sh | sh`
3. **Download model**: `ollama pull llama3.2`
4. **Save script**: Save `audio2note-ollama.sh` from Method 1
5. **Run**: `./audio2note-ollama.sh lecture.mp3`

**Time**: 30 min setup, fully automated
**Cost**: $0 forever

### Advanced: Automated + Best Quality

1. **Install Whisper.cpp**: See installation section above
2. **Get Claude API key**: Sign up at console.anthropic.com
3. **Save script**: Save `audio2note.sh` from Method 1
4. **Set API key**: `export ANTHROPIC_API_KEY="your-key"`
5. **Run**: `./audio2note.sh lecture.mp3`

**Time**: 30 min setup, fully automated
**Cost**: ~$0.03/hour of audio

### Expert: Web App on Server

1. **Install Whisper.cpp on frodo**: See installation section
2. **Install Ollama** (free) or set up Claude API
3. **Deploy Flask app**: See Method 3 above
4. **Access from any device**: `http://frodo:5000`

**Time**: 1-2 hours setup
**Cost**: $0 with Ollama, ~$0.03/hr with Claude API

## Recommended Setups

### Option A: Laptop Only (Fully Portable)

```
┌──────────────────────────────────────────┐
│ Laptop: Record or download audio        │
└───────────────┬──────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────┐
│ Whisper.cpp (local transcription)       │
│ Model: base or small                    │
└───────────────┬──────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────┐
│ Ollama (local formatting) - FREE        │
│ OR Claude.ai (copy-paste) - FREE        │
└───────────────┬──────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────┐
│ Save .md file locally                    │
└──────────────────────────────────────────┘
```

**Cost**: $0 | **Privacy**: 100% with Ollama | **Setup**: 30 min

### Option B: Phone Only (On-the-Go)

```
┌──────────────────────────────────────────┐
│ Phone: Record voice memo                │
└───────────────┬──────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────┐
│ Termux + Whisper.cpp (transcription)    │
│ Model: tiny or base                     │
└───────────────┬──────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────┐
│ Claude.ai mobile (format transcript)    │
└───────────────┬──────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────┐
│ Save to Notes app                        │
└──────────────────────────────────────────┘
```

**Cost**: $0 | **Privacy**: Transcription local | **Setup**: 20 min

### Option C: Server-Based (Your Infrastructure)

```
┌─────────────────────────────────────────────┐
│ Any Device: Upload to Nextcloud            │
│ /nextcloud/Audio/to_process/               │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│ Frodo: Whisper.cpp (transcription)         │
│ Model: small or medium (8GB RAM)           │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│ Frodo: Ollama (formatting) - 100% FREE     │
│ OR Claude API - $0.03/hour                 │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│ Nextcloud: Save .md notes                  │
│ /nextcloud/Notes/from_audio/               │
└─────────────────────────────────────────────┘
```

**Benefits:**
- ✅ 100% private (audio never leaves your network)
- ✅ Completely free with Ollama
- ✅ Automated (drop file → get notes)
- ✅ Integrated with existing backup system
- ✅ Access from phone, laptop, anywhere

### Option D: Web App (Best User Experience)

```
┌─────────────────────────────────────────────┐
│ Any Device: Open http://frodo:5000         │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│ Web Interface: Upload audio file           │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│ Frodo: Whisper.cpp + Ollama                │
│ Processing happens server-side             │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│ Download .md file or save to Nextcloud     │
└─────────────────────────────────────────────┘
```

**Use Case:** Family members can use it too!

## Recommended Choice

**For you personally:**
- **Quick start**: Option A (laptop with Ollama) - 100% free, private, fast
- **Best overall**: Option C (server-based) - Set it up once, use from anywhere
- **For family/sharing**: Option D (web app) - Easy for anyone to use

## Summary: Best Practices

### Platform Recommendations

| Use Case | Platform | Transcription | Formatting | Cost | Setup Time |
|----------|----------|---------------|------------|------|------------|
| **Quick test** | Laptop | Whisper.cpp base | Claude.ai free | $0 | 10 min |
| **Daily use** | Laptop | Whisper.cpp small | Ollama | $0 | 30 min |
| **Voice memos** | Phone | Whisper.cpp tiny | Claude.ai mobile | $0 | 20 min |
| **Home automation** | Server (frodo) | Whisper.cpp medium | Ollama | $0 | 1-2 hours |
| **Best quality** | Server/Laptop | Whisper.cpp medium | Claude API | $0.03/hr | 30 min |
| **Family sharing** | Web app (frodo) | Whisper.cpp small | Ollama | $0 | 2 hours |

### Key Takeaways

1. **Whisper.cpp is the core** - Fast, free, accurate, runs anywhere
2. **Ollama makes it 100% free** - No API costs, unlimited usage, good quality
3. **Phone works!** - Termux + Whisper.cpp tiny model = portable transcription
4. **Web app = best UX** - Host on frodo, access from anywhere
5. **Privacy first** - Everything can run locally (no cloud needed)

## Resources

### Essential Tools
- [Whisper.cpp](https://github.com/ggerganov/whisper.cpp) - Core transcription (REQUIRED)
- [Ollama](https://ollama.com/) - Free local AI formatting (RECOMMENDED)
- [FFmpeg](https://ffmpeg.org/) - Audio processing (optional)
- [Termux](https://f-droid.org/en/packages/com.termux/) - Android terminal (for phone setup)

### AI Services
- [Claude.ai](https://claude.ai/) - Free tier for formatting (no API)
- [Anthropic API](https://console.anthropic.com/) - Paid API for automation
- [ChatGPT](https://chatgpt.com/) - Alternative free tier

### Advanced (Optional)
- [PyAnnote](https://github.com/pyannote/pyannote-audio) - Speaker diarization
- [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper) - Even faster than whisper.cpp

---

## Next Steps

**Absolute beginner:**
1. Install Whisper.cpp on laptop (10 min)
2. Transcribe a test audio file
3. Copy-paste to Claude.ai for formatting
4. Done!

**Want automation:**
1. Install Whisper.cpp + Ollama (30 min)
2. Save the `audio2note-ollama.sh` script
3. Run `audio2note-ollama.sh yourfile.mp3`
4. Get formatted markdown instantly!

**Want web interface:**
1. Set up Whisper.cpp + Ollama on frodo
2. Deploy the Flask web app
3. Access from phone/laptop: `http://frodo:5000`
4. Upload audio, download markdown!

**Start simple, expand later!** The basic Whisper.cpp + Claude.ai combo is powerful enough for most needs.


**Created:** 2025-11-09

