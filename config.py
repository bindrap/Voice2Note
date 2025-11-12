import os

class Config:
    """Application configuration"""

    # Base directory
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # Paths
    TEMP_DIR = os.path.join(BASE_DIR, 'temp')
    NOTES_DIR = os.path.join(BASE_DIR, 'notes')
    MODELS_DIR = os.path.join(BASE_DIR, 'models')
    DATABASE_PATH = os.path.join(BASE_DIR, 'voice2note.db')

    # Whisper configuration
    WHISPER_MODEL = os.getenv('WHISPER_MODEL', 'medium')  # Changed from large-v3 for 2-3x faster transcription
    WHISPER_PATH = os.path.join(BASE_DIR, 'Whisper', 'build', 'bin', 'whisper-cli')
    WHISPER_MODEL_PATH = os.path.join(BASE_DIR, 'Whisper', 'models', f'ggml-{WHISPER_MODEL}.bin')

    # yt-dlp configuration (use global installation)
    YT_DLP_PATH = '/usr/local/bin/yt-dlp'

    # Ollama configuration
    OLLAMA_API_KEY = os.getenv('OLLAMA_API_KEY', '1728cbe73f944db7afa1a3c8f52d2f41.GzEVZ8ADdcDHwIxdbvKnqbXy')
    OLLAMA_HOST = 'https://ollama.com'
    OLLAMA_MODEL = 'gpt-oss:120b'

    # Flask configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 'yes')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_UPLOAD_SIZE', 500)) * 1024 * 1024  # Default 500MB
    UPLOAD_FOLDER = TEMP_DIR

    # Network configuration
    HOST = os.getenv('HOST', '0.0.0.0')  # Listen on all interfaces (Tailscale compatible)
    PORT = int(os.getenv('PORT', 5000))

    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm', 'flv', 'wmv', 'mp3', 'wav', 'm4a'}

    @staticmethod
    def init_app():
        """Initialize application directories"""
        os.makedirs(Config.TEMP_DIR, exist_ok=True)
        os.makedirs(Config.NOTES_DIR, exist_ok=True)
        os.makedirs(Config.MODELS_DIR, exist_ok=True)
