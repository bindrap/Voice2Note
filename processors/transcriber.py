import os
import subprocess
import json
from config import Config


class Transcriber:
    """Handles audio transcription using whisper.cpp"""

    def __init__(self):
        self.whisper_path = Config.WHISPER_PATH
        self.model_path = Config.WHISPER_MODEL_PATH

    def check_whisper_installed(self):
        """Check if whisper.cpp is installed and model exists"""
        if not os.path.exists(self.whisper_path):
            raise FileNotFoundError(
                f"whisper.cpp not found at {self.whisper_path}\n"
                f"Please install whisper.cpp and build it:\n"
                f"  git clone https://github.com/ggml-org/whisper.cpp\n"
                f"  cd whisper.cpp\n"
                f"  cmake -B build && cmake --build build -j --config Release"
            )

        if not os.path.exists(self.model_path):
            raise FileNotFoundError(
                f"Whisper model not found at {self.model_path}\n"
                f"Please download the model:\n"
                f"  cd whisper.cpp\n"
                f"  bash ./models/download-ggml-model.sh {Config.WHISPER_MODEL}"
            )

        return True

    def transcribe(self, audio_path, language='en', output_format='txt'):
        """
        Transcribe audio file using whisper.cpp

        Args:
            audio_path: Path to audio file (WAV format)
            language: Language code (e.g., 'en', 'es')
            output_format: Output format ('txt', 'json', 'srt')

        Returns:
            dict with transcript_text and timestamps (if available)
        """
        # Verify whisper is installed
        self.check_whisper_installed()

        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Prepare output path
        base_name = os.path.splitext(audio_path)[0]
        output_file = f"{base_name}.txt"
        json_file = f"{base_name}.json"

        print(f"Transcribing: {audio_path}")
        print(f"Using model: {self.model_path}")

        try:
            # Run whisper.cpp
            # Note: Adjust command based on actual whisper.cpp build
            cmd = [
                self.whisper_path,
                '-m', self.model_path,
                '-f', audio_path,
                '-l', language,
                '-otxt',  # Output as text
                '-of', base_name,  # Output file base name
                '--threads', '4',  # Number of threads (matches CPU cores)
                '--processors', '1',  # Single processor for sequential processing
                '--print-progress',
            ]

            print(f"Running: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            print("Transcription completed!")
            print(f"Output: {result.stdout}")

            # Read the transcript
            if os.path.exists(output_file):
                with open(output_file, 'r', encoding='utf-8') as f:
                    transcript_text = f.read().strip()
            else:
                raise FileNotFoundError(f"Transcript file not created: {output_file}")

            # Try to read JSON output if it exists (for timestamps)
            timestamps = None
            if os.path.exists(json_file):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)
                        timestamps = json_data.get('transcription', [])
                except:
                    pass

            # Cleanup output files
            if os.path.exists(output_file):
                os.remove(output_file)
            if os.path.exists(json_file):
                os.remove(json_file)

            return {
                'transcript_text': transcript_text,
                'timestamps': timestamps,
                'language': language,
            }

        except subprocess.CalledProcessError as e:
            raise Exception(
                f"Transcription failed:\n"
                f"Command: {' '.join(cmd)}\n"
                f"Error: {e.stderr}"
            )
        except Exception as e:
            raise Exception(f"Transcription error: {str(e)}")

    def chunk_transcript(self, transcript_text, chunk_size=5000):
        """
        Split long transcript into chunks for processing

        Args:
            transcript_text: Full transcript text
            chunk_size: Maximum characters per chunk

        Returns:
            list of text chunks
        """
        if len(transcript_text) <= chunk_size:
            return [transcript_text]

        chunks = []
        sentences = transcript_text.split('. ')
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence_length = len(sentence) + 2  # +2 for '. '

            if current_length + sentence_length > chunk_size and current_chunk:
                # Save current chunk
                chunks.append('. '.join(current_chunk) + '.')
                current_chunk = [sentence]
                current_length = sentence_length
            else:
                current_chunk.append(sentence)
                current_length += sentence_length

        # Add last chunk
        if current_chunk:
            chunks.append('. '.join(current_chunk) + '.')

        return chunks
