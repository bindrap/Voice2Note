# Whisper.cpp Complete Guide

## Overview

**whisper.cpp** is a C/C++ implementation of OpenAI's Whisper automatic speech recognition model for converting audio to text. It's faster and more efficient than the Python version.

**Why Whisper.cpp?**
- ✅ Completely free and private (no cloud needed)
- ✅ Fast (2-10x faster than Python Whisper)
- ✅ Runs on laptop, phone (Termux), or as web service
- ✅ Low resource usage (works on CPU, GPU optional)
- ✅ Cross-platform (Linux, macOS, Windows, Android)

## Quick Start

### 1. Clone and Build

```bash
git clone https://github.com/ggml-org/whisper.cpp.git
cd whisper.cpp

# Build
cmake -B build
cmake --build build -j --config Release
```

### 2. Download a Model

```bash
# English-only models (faster, smaller)
sh ./models/download-ggml-model.sh base.en
sh ./models/download-ggml-model.sh small.en

# Multilingual models
sh ./models/download-ggml-model.sh base
sh ./models/download-ggml-model.sh medium
```

### 3. Transcribe Audio

```bash
./build/bin/whisper-cli -f samples/jfk.wav
```

## Audio Format Requirements

**Important:** whisper-cli works best with 16-bit WAV files.

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

| Model     | Disk Size | Memory Usage | Accuracy |
|-----------|-----------|--------------|----------|
| tiny      | 75 MiB    | ~273 MB      | Fair (85%) |
| base      | 142 MiB   | ~388 MB      | Good (90%) |
| small     | 466 MiB   | ~852 MB      | Very good (94%) |
| medium    | 1.5 GiB   | ~2.1 GB      | Excellent (97%) |
| large     | 2.9 GiB   | ~3.9 GB      | Best (98%) |

### Model Selection Guide

- **Phone**: Use `tiny` or `base`
- **Laptop**: Use `base` or `small` for daily use
- **Server**: Use `small` or `medium`
- **Technical content**: Use at least `small`, preferably `medium`
- **Professional use**: Use `large`

## Common Use Cases

### Basic Transcription

```bash
./build/bin/whisper-cli -m models/ggml-base.en.bin -f samples/jfk.wav
```

### Word-Level Timestamps

```bash
./build/bin/whisper-cli -m models/ggml-base.en.bin -f samples/jfk.wav -ml 1
```

### Output to Text File

```bash
./build/bin/whisper-cli -m models/ggml-base.en.bin -f audio.wav -otxt
```

### With Language Specification (faster)

```bash
./build/bin/whisper-cli -m models/ggml-base.en.bin -f audio.wav -l en
```

### Voice Activity Detection (VAD)

```bash
# Download VAD model
./models/download-vad-model.sh silero-v5.1.2

# Use with whisper
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

### Apple Silicon (Metal/Core ML)

```bash
cmake -B build -DWHISPER_COREML=1
cmake --build build -j --config Release
```

### Vulkan (Cross-platform GPU)

```bash
cmake -B build -DGGML_VULKAN=1
cmake --build build -j --config Release
```

## Advanced Features

### Model Quantization

Reduce model size and memory usage:

```bash
# Quantize model
./build/bin/quantize models/ggml-base.en.bin models/ggml-base.en-q5_0.bin q5_0

# Use quantized model
./build/bin/whisper-cli -m models/ggml-base.en-q5_0.bin ./samples/jfk.wav
```

### FFmpeg Support (More Audio Formats)

Linux:

```bash
# Install dependencies
sudo apt install libavcodec-dev libavformat-dev libavutil-dev

# Build with FFmpeg
cmake -B build -DWHISPER_FFMPEG=yes
cmake --build build -j --config Release

# Now you can use various formats
./build/bin/whisper-cli --model models/ggml-base.en.bin --file audio.opus
```

## Command-Line Options

Common options:
- `-f FILE`: Input audio file
- `-m MODEL`: Model file path
- `-t N`: Number of threads (default: 4)
- `-l LANG`: Language code (e.g., "en", "es", "fr")
- `-ml N`: Maximum segment length in characters
- `-otxt`: Output to text file
- `-oj`: Output to JSON file
- `--print-colors`: Color-code transcription by confidence
- `--vad`: Enable Voice Activity Detection

Get full help:
```bash
./build/bin/whisper-cli -h
```

## Hardware Requirements

### Device Compatibility

| Device | Model | RAM | Time (1hr audio) | Best Use |
|--------|-------|-----|------------------|----------|
| Phone (Termux) | tiny | 2GB | ~2 hours | Voice memos |
| Phone (Termux) | base | 4GB | ~3 hours | Recordings |
| Laptop (CPU) | base | 4GB | ~30-60 min | General use |
| Laptop (CPU) | small | 4GB | ~45-90 min | Better accuracy |
| Laptop (CPU) | medium | 8GB | ~90-180 min | Technical content |
| Desktop (GPU) | large | 10GB | ~6-12 min | Production |

## Audio to Markdown Notes Workflow

### The Two-Step Process

1. **Audio → Text**: Transcription with Whisper.cpp
2. **Text → Markdown**: Formatting with AI

### Complete Automation Script

```bash
#!/bin/bash
# audio2note.sh - Whisper.cpp + AI formatting

AUDIO_FILE="$1"
BASE_NAME=$(basename "$AUDIO_FILE" | sed 's/\.[^.]*$//')
WHISPER_MODEL="${WHISPER_MODEL:-$HOME/whisper.cpp/models/ggml-base.bin}"

# Step 1: Transcribe with whisper.cpp
echo "Transcribing with whisper.cpp..."
~/whisper.cpp/build/bin/whisper-cli \
  -m "$WHISPER_MODEL" \
  -f "$AUDIO_FILE" \
  -l en \
  -otxt \
  -of "/tmp/${BASE_NAME}"

TRANSCRIPT=$(cat "/tmp/${BASE_NAME}.txt")

# Step 2: Format with AI (use your preferred AI service)
echo "Formatting notes with AI..."
# ... AI formatting code here ...

echo "✓ Notes saved to: ${BASE_NAME}.md"
rm "/tmp/${BASE_NAME}.txt"
```

### Using with Ollama (Free, Local)

```bash
#!/bin/bash
# audio2note-ollama.sh - 100% free & private

AUDIO_FILE="$1"
BASE_NAME=$(basename "$AUDIO_FILE" | sed 's/\.[^.]*$//')
WHISPER_MODEL="${WHISPER_MODEL:-$HOME/whisper.cpp/models/ggml-base.bin}"

# Step 1: Transcribe
echo "Transcribing..."
~/whisper.cpp/build/bin/whisper-cli \
  -m "$WHISPER_MODEL" \
  -f "$AUDIO_FILE" \
  -l en \
  -otxt \
  -of "/tmp/${BASE_NAME}"

TRANSCRIPT=$(cat "/tmp/${BASE_NAME}.txt")

# Step 2: Format with Ollama (local AI)
echo "Formatting notes..."
FORMATTED_NOTES=$(ollama run llama3.2 "Convert this transcript into well-structured markdown notes with headings, bullet points, and key takeaways:\n\n$TRANSCRIPT")

echo "$FORMATTED_NOTES" > "${BASE_NAME}.md"
echo "✓ Notes saved to: ${BASE_NAME}.md"
rm "/tmp/${BASE_NAME}.txt"
```

## Improving Transcription Accuracy

### Pre-Processing Audio

```bash
# Convert to optimal format (16kHz mono WAV)
ffmpeg -i input.mp3 -ar 16000 -ac 1 output.wav

# Reduce background noise
ffmpeg -i input.mp3 -af "highpass=f=200, lowpass=f=3000" cleaned.mp3

# Normalize volume
ffmpeg -i input.mp3 -af "loudnorm" normalized.mp3
```

### Best Practices

- Better audio quality = better transcription
- Use at least `small` model for technical content
- Use `medium` for medical/legal terminology
- Specify language with `-l en` for 20-30% speedup
- Use initial prompt for context: `--prompt "This is about quantum physics"`

## AI Formatting Prompts

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

## Cost Analysis

### For 1 Hour of Audio

| Method | Transcription | Formatting | Total | Notes |
|--------|---------------|------------|-------|-------|
| Whisper.cpp + Ollama | $0.00 | $0.00 | $0.00 | 100% Free |
| Whisper.cpp + Claude API | $0.00 | $0.03 | $0.03 | Best quality |
| Whisper.cpp + ChatGPT | $0.00 | $0.02 | $0.02 | Alternative |

**Bottom line:** Transcription is FREE with Whisper.cpp!

## Installation on Different Platforms

### Laptop (Linux/macOS/Windows)

```bash
# Clone repository
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp

# Build
cmake -B build
cmake --build build -j --config Release

# Download models
bash ./models/download-ggml-model.sh base
```

### Phone (Android with Termux)

```bash
# Install Termux from F-Droid
# Open Termux and run:

pkg update && pkg upgrade
pkg install git clang make cmake

# Clone and build
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp
cmake -B build
cmake --build build -j

# Download tiny model (lighter for phone)
bash ./models/download-ggml-model.sh tiny

# Set up storage access
termux-setup-storage

# Transcribe
./build/bin/whisper-cli -m models/ggml-tiny.bin -f ~/storage/shared/recording.wav -otxt
```

### Docker Usage

```bash
# Download model
docker run -it --rm \
  -v path/to/models:/models \
  ghcr.io/ggml-org/whisper.cpp:main "./models/download-ggml-model.sh base /models"

# Transcribe audio
docker run -it --rm \
  -v path/to/models:/models \
  -v path/to/audios:/audios \
  ghcr.io/ggml-org/whisper.cpp:main "whisper-cli -m /models/ggml-base.bin -f /audios/audio.wav"
```

### With CUDA Support

```bash
docker run -it --rm --gpus all \
  -v path/to/models:/models \
  -v path/to/audios:/audios \
  ghcr.io/ggml-org/whisper.cpp:main-cuda "whisper-cli -m /models/ggml-base.bin -f /audios/audio.wav"
```

## Troubleshooting

### Audio File Not Working

Ensure your audio is in the correct format:
```bash
ffmpeg -i input.mp3 -ar 16000 -ac 1 -c:a pcm_s16le output.wav
```

### Out of Memory

- Use a smaller model (e.g., `tiny` or `base`)
- Use quantization
- Process in chunks
- Close other applications

### Slow Performance

- Use GPU acceleration (CUDA, Metal, Vulkan)
- Use a smaller model
- Enable VAD to skip non-speech segments
- Increase thread count with `-t` flag
- Specify language with `-l` for faster processing

### Low Accuracy

- Use better audio source
- Pre-process audio (denoise, normalize)
- Use larger Whisper model
- Specify language explicitly
- Add context with `--prompt`

## Advanced Features

### Speaker Diarization

```python
# Using pyannote.audio
from pyannote.audio import Pipeline

pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization")
diarization = pipeline("audio.wav")

# Output: Speaker A: 0s-15s, Speaker B: 15s-32s, etc.
```

### Timestamp Preservation

```bash
# Whisper with timestamps
./build/bin/whisper-cli -m models/ggml-base.bin -f audio.wav --output-srt

# Creates .srt subtitle file with timestamps
```

### Multi-Language Support

```bash
# Auto-detect language
./build/bin/whisper-cli -m models/ggml-base.bin -f audio.wav

# Specify language
./build/bin/whisper-cli -m models/ggml-base.bin -f audio.wav -l es

# Translate to English
./build/bin/whisper-cli -m models/ggml-base.bin -f audio.wav --translate
```

## Performance Benchmarks

**Laptop**: 1-3x real-time (20-60 min for 1 hour audio)
**Desktop with GPU**: 5-10x real-time (6-12 min for 1 hour audio)
**Phone (Termux)**: 0.5x real-time (2 hours for 1 hour audio with tiny model)

## Resources

### Essential Links
- [Whisper.cpp Repository](https://github.com/ggml-org/whisper.cpp)
- [Model Downloads](https://github.com/ggml-org/whisper.cpp/tree/master/models)
- [Discussions](https://github.com/ggml-org/whisper.cpp/discussions)
- [FAQ](https://github.com/ggml-org/whisper.cpp/discussions/126)

### Related Tools
- [FFmpeg](https://ffmpeg.org/) - Audio processing
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube downloader
- [Ollama](https://ollama.com/) - Local AI for formatting
- [PyAnnote](https://github.com/pyannote/pyannote-audio) - Speaker diarization

## Quick Start Examples

### Beginner (Manual)

1. Install Whisper.cpp (5 min)
2. Transcribe: `./build/bin/whisper-cli -m models/ggml-base.bin -f audio.mp3 -otxt`
3. Format: Copy transcript to AI service
4. Save: Copy result to `.md` file

**Time**: 10 min setup, 2 min per file
**Cost**: $0

### Intermediate (Automated)

1. Install Whisper.cpp
2. Install Ollama: `curl -fsSL https://ollama.com/install.sh | sh`
3. Download model: `ollama pull llama3.2`
4. Save automation script
5. Run: `./audio2note.sh lecture.mp3`

**Time**: 30 min setup, fully automated
**Cost**: $0 forever

### Advanced (Web Interface)

1. Set up Whisper.cpp on server
2. Install Flask web app
3. Access from any device
4. Upload audio, download markdown

**Time**: 1-2 hours setup
**Cost**: $0 with Ollama

## Summary

Whisper.cpp is the ideal solution for:
- ✅ Free, private transcription
- ✅ Fast processing
- ✅ Cross-platform support
- ✅ Low resource requirements
- ✅ High accuracy
- ✅ Flexible deployment options

**Best combination**: Whisper.cpp for transcription + Ollama for formatting = 100% free, private, and powerful note-taking system!
