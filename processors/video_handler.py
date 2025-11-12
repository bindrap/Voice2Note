import os
import subprocess
import json
from config import Config


class VideoHandler:
    """Handles video/audio extraction from various sources"""

    def __init__(self):
        self.temp_dir = Config.TEMP_DIR
        # Look for cookies.txt in project root
        self.cookies_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cookies.txt')

    def is_youtube_url(self, source):
        """Check if source is a YouTube URL"""
        return 'youtube.com' in source or 'youtu.be' in source

    def download_youtube_audio(self, url):
        """
        Download video from YouTube, extract audio, delete video
        Returns: dict with audio_path and metadata
        """
        # Use global yt-dlp binary
        yt_dlp_bin = Config.YT_DLP_PATH

        # Extract video ID from URL
        import re
        video_id_match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', url)
        if video_id_match:
            video_id = video_id_match.group(1)
        else:
            video_id = 'unknown'

        print(f"Processing YouTube video: {video_id}")

        # Download video file (this works reliably and gets metadata)
        video_file = None
        output_template = os.path.join(self.temp_dir, f"{video_id}.%(ext)s")

        try:
            print("Downloading video...")
            download_cmd = [
                yt_dlp_bin,
                '-o', output_template,
                '--no-playlist',
                '--cookies-from-browser', 'firefox',
                url
            ]

            result = subprocess.run(
                download_cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=1800  # 30 minutes timeout
            )

            # Find the downloaded video file (could be .mp4, .webm, etc.)
            possible_extensions = ['mp4', 'webm', 'mkv', 'flv']
            video_file = None
            for ext in possible_extensions:
                test_path = os.path.join(self.temp_dir, f"{video_id}.{ext}")
                if os.path.exists(test_path):
                    video_file = test_path
                    break

            if not video_file or not os.path.exists(video_file):
                raise Exception(f"Video file not found after download")

            print(f"✓ Video downloaded: {video_file}")

            # Extract audio using ffmpeg
            audio_path = os.path.join(self.temp_dir, f"{video_id}.wav")
            print(f"Extracting audio to: {audio_path}")

            ffmpeg_cmd = [
                'ffmpeg',
                '-i', video_file,
                '-vn',  # No video
                '-acodec', 'pcm_s16le',  # 16-bit PCM
                '-ar', '16000',  # 16kHz sample rate (Whisper requirement)
                '-ac', '1',  # Mono
                '-y',  # Overwrite output file
                audio_path
            ]

            subprocess.run(ffmpeg_cmd, capture_output=True, text=True, check=True, timeout=600)

            if not os.path.exists(audio_path):
                raise Exception(f"Audio extraction failed - file not created: {audio_path}")

            # Delete the video file to save space
            print(f"Deleting video file: {video_file}")
            os.remove(video_file)

            print(f"✓ Audio extracted successfully: {audio_path}")

            # Try to get metadata after successful download
            try:
                info_cmd = [
                    yt_dlp_bin,
                    '--dump-json',
                    '--no-playlist',
                    '--cookies-from-browser', 'firefox',
                    url
                ]
                result = subprocess.run(info_cmd, capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    info = json.loads(result.stdout)
                else:
                    info = {}
            except:
                info = {}

            return {
                'audio_path': audio_path,
                'title': info.get('title', f'YouTube Video {video_id}'),
                'channel': info.get('uploader', 'Unknown'),
                'duration': info.get('duration', 0),
                'video_id': video_id,
                'url': url,
                'description': info.get('description', ''),
                'chapters': info.get('chapters', []),
            }

        except subprocess.CalledProcessError as e:
            error_msg = f"Command failed: {e.stderr if e.stderr else str(e)}"
            print(f"✗ Failed: {error_msg}")
            # Try to cleanup video file if it exists
            if video_file and os.path.exists(video_file):
                try:
                    os.remove(video_file)
                except:
                    pass
            raise Exception(error_msg)
        except Exception as e:
            # Try to cleanup video file if it exists
            if video_file and os.path.exists(video_file):
                try:
                    os.remove(video_file)
                except:
                    pass
            raise Exception(f"Failed to download YouTube audio: {e}")

    def extract_local_audio(self, video_path, video_id=None):
        """
        Extract audio from local video file
        Returns: dict with audio_path and metadata
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # Generate unique filename
        if video_id:
            audio_filename = f"{video_id}.wav"
        else:
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            audio_filename = f"{base_name}.wav"

        audio_path = os.path.join(self.temp_dir, audio_filename)

        # Extract audio using ffmpeg
        try:
            subprocess.run([
                'ffmpeg', '-i', video_path,
                '-vn',  # No video
                '-acodec', 'pcm_s16le',  # 16-bit PCM
                '-ar', '16000',  # 16kHz sample rate
                '-ac', '1',  # Mono
                '-y',  # Overwrite output file
                audio_path
            ], check=True, capture_output=True, text=True)

            # Get video duration
            duration = self._get_video_duration(video_path)

            return {
                'audio_path': audio_path,
                'title': os.path.basename(video_path),
                'channel': 'Local Upload',
                'duration': duration,
                'video_id': video_id or base_name,
                'url': None,
                'description': '',
                'chapters': [],
            }
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to extract audio: {e.stderr}")

    def _get_video_duration(self, video_path):
        """Get video duration in seconds using ffprobe"""
        try:
            result = subprocess.run([
                'ffprobe', '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                video_path
            ], capture_output=True, text=True, check=True)

            return int(float(result.stdout.strip()))
        except:
            return 0

    def process_source(self, source, is_file=False, file_path=None):
        """
        Process video source (YouTube URL or local file)
        Returns: dict with audio_path and metadata
        """
        if is_file and file_path:
            print(f"Processing local file: {file_path}")
            return self.extract_local_audio(file_path)
        elif self.is_youtube_url(source):
            print(f"Processing YouTube URL: {source}")
            return self.download_youtube_audio(source)
        else:
            raise ValueError("Invalid source: Must be YouTube URL or local file")

    def cleanup_audio(self, audio_path):
        """Remove temporary audio file"""
        if os.path.exists(audio_path):
            try:
                os.remove(audio_path)
                print(f"Cleaned up: {audio_path}")
            except Exception as e:
                print(f"Warning: Failed to cleanup {audio_path}: {e}")
