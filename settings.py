from dotenv import load_dotenv
import os

load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# Server Settings
PORT = int(os.getenv('PORT', 5000))
HOST = os.getenv('HOST', '0.0.0.0')
DEBUG = os.getenv('DEBUG') == 'True'

# Database Settings
DB_DIRECTORY = os.getenv('DB_DIRECTORY')
COLLECTION_NAME = os.getenv('COLLECTION_NAME')

# Model Settings
LOCAL_MODEL_NAME = os.getenv('LOCAL_MODEL_NAME')
GEMINI_MODEL_NAME = os.getenv('GEMINI_MODEL_NAME')  # اصلاح شده از gimini_model
OPENAI_MODEL_NAME = os.getenv('OPENAI_MODEL_NAME')

# Embeddings Settings
EMBEDDING_MODEL_NAME = os.getenv('EMBEDDING_MODEL_NAME')
CHUNK_SIZE = os.getenv('CHUNK_SIZE')

# API Rate Limits
MAX_TOKENS = os.getenv('MAX_TOKENS')
TOKENS_PER_MIN = os.getenv('TOKENS_PER_MIN')

# Security
SECRET_KEY = os.getenv('SECRET_KEY')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS')