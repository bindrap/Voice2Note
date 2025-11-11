import os
import subprocess
import yt_dlp
from config import Config


class VideoHandler:
    """Handles video/audio extraction from various sources"""

    def __init__(self):
        self.temp_dir = Config.TEMP_DIR

    def is_youtube_url(self, source):
        """Check if source is a YouTube URL"""
        return 'youtube.com' in source or 'youtu.be' in source

    def download_youtube_audio(self, url):
        """
        Download audio from YouTube video
        Returns: dict with audio_path and metadata
        """
        output_template = os.path.join(self.temp_dir, '%(id)s.%(ext)s')

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
            'outtmpl': output_template,
            'quiet': False,
            'no_warnings': False,
            # Enhanced options to bypass 403 errors
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                    'player_skip': ['webpage', 'configs'],
                }
            },
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Sec-Fetch-Mode': 'navigate',
            },
        }

        try:
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
            raise Exception(f"Failed to download YouTube video: {str(e)}")

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
