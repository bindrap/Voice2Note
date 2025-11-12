import os
import subprocess
import yt_dlp
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
        Download audio from YouTube video
        Returns: dict with audio_path and metadata
        """
        output_template = os.path.join(self.temp_dir, '%(id)s.%(ext)s')

        # Base options that work for most videos
        base_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
            'outtmpl': output_template,
            'quiet': False,
            'no_warnings': False,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'no_color': True,
            'extract_flat': False,
        }

        # Try different configurations in order of preference
        config_attempts = []

        # If cookies.txt exists, try it first
        if os.path.exists(self.cookies_file):
            print(f"Found cookies.txt at {self.cookies_file}")
            config_attempts.append({
                **base_opts,
                'cookiefile': self.cookies_file,
                'extractor_args': {
                    'youtube': {
                        'player_client': ['ios', 'android', 'web'],
                    }
                },
            })

        # Standard attempts
        config_attempts.extend([
            # Attempt 1: iOS client (works for most videos)
            {
                **base_opts,
                'extractor_args': {
                    'youtube': {
                        'player_client': ['ios'],
                        'player_skip': ['configs'],
                    }
                },
                'http_headers': {
                    'User-Agent': 'com.google.ios.youtube/19.29.1 (iPhone16,2; U; CPU iOS 17_5_1 like Mac OS X;)',
                },
            },
            # Attempt 2: Android client with browser cookies
            {
                **base_opts,
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android', 'web'],
                    }
                },
                'cookiesfrombrowser': ('chrome',),
            },
            # Attempt 3: Try firefox cookies
            {
                **base_opts,
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android', 'web'],
                    }
                },
                'cookiesfrombrowser': ('firefox',),
            },
            # Attempt 4: Basic android client without cookies
            {
                **base_opts,
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android'],
                    }
                },
            },
        ])

        last_error = None
        for i, ydl_opts in enumerate(config_attempts):
            try:
                print(f"Download attempt {i+1}/{len(config_attempts)}...")
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)

                    audio_path = os.path.join(self.temp_dir, f"{info['id']}.wav")

                    return {
                        'audio_path': audio_path,
                        'title': info.get('title', 'Unknown'),
                        'channel': info.get('uploader', 'Unknown'),
                        'duration': info.get('duration', 0),
                        'video_id': info.get('id', ''),
                        'url': url,
                        'description': info.get('description', ''),
                        'chapters': info.get('chapters', []),
                    }
            except Exception as e:
                last_error = str(e)
                print(f"Attempt {i+1} failed: {e}")
                continue

        # All attempts failed
        raise Exception(f"Failed to download YouTube video after {len(config_attempts)} attempts. Last error: {last_error}")

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
