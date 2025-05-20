from decouple import config

# Server Settings
PORT = config('PORT', default=5000, cast=int)
HOST = config('HOST', default='0.0.0.0')
DEBUG = config('DEBUG', default=True, cast=bool)

# Database Settings
DB_DIRECTORY = config('DB_DIRECTORY', default='knowledge_base')
COLLECTION_NAME = config('COLLECTION_NAME', default='website_data')

# Model Settings
LOCAL_MODEL_NAME = config('LOCAL_MODEL_NAME', default='llama3.2:latest')
GEMINI_MODEL_NAME = config('GEMINI_MODEL_NAME', default='gemini-2.0-flash')
OPENAI_MODEL_NAME = config('OPENAI_MODEL_NAME', default='gpt-4.1-nano')

# API Keys
OPENAI_API_KEY = config('OPENAI_API_KEY')
GOOGLE_API_KEY = config('GOOGLE_API_KEY')

# Embeddings Settings
EMBEDDING_MODEL_NAME = config('EMBEDDING_MODEL_NAME', default='all-MiniLM-L6-v2')
CHUNK_SIZE = config('CHUNK_SIZE', default=500, cast=int)

# API Rate Limits
MAX_TOKENS = config('MAX_TOKENS', default=8000, cast=int)
TOKENS_PER_MIN = config('TOKENS_PER_MIN', default=30000, cast=int)

# Security
SECRET_KEY = config('SECRET_KEY')
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

# Chat Settings
MAX_CHAT_HISTORY = config('MAX_CHAT_HISTORY', default=7, cast=int)
SIMILARITY_THRESHOLD = config('SIMILARITY_THRESHOLD', default=0.5, cast=float)