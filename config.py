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
    WHISPER_MODEL = 'medium'
    WHISPER_PATH = os.path.join(BASE_DIR, 'Whisper', 'build', 'bin', 'whisper-cli')
    WHISPER_MODEL_PATH = os.path.join(BASE_DIR, 'Whisper', 'models', 'ggml-medium.bin')

    # Ollama configuration
    OLLAMA_API_KEY = os.getenv('OLLAMA_API_KEY', '1728cbe73f944db7afa1a3c8f52d2f41.GzEVZ8ADdcDHwIxdbvKnqbXy')
    OLLAMA_HOST = 'https://ollama.com'
    OLLAMA_MODEL = 'gpt-oss:120b'

    # Flask configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    DEBUG = True
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB max file size
    UPLOAD_FOLDER = TEMP_DIR

    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm', 'flv', 'wmv', 'mp3', 'wav', 'm4a'}

    @staticmethod
    def init_app():
        """Initialize application directories"""
        os.makedirs(Config.TEMP_DIR, exist_ok=True)
        os.makedirs(Config.NOTES_DIR, exist_ok=True)
        os.makedirs(Config.MODELS_DIR, exist_ok=True)
