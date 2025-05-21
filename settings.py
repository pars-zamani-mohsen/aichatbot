import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')

# Server settings
PORT = int(os.getenv('PORT', 5000))
HOST = os.getenv('HOST', '127.0.0.1')
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

# Database settings
DB_DIRECTORY = os.getenv('DB_DIRECTORY', 'processed_data')
COLLECTION_NAME = os.getenv('COLLECTION_NAME', 'parsicanada')

# Model settings
MAX_TOKENS = int(os.getenv('MAX_TOKENS', 2000))
TOKENS_PER_MIN = int(os.getenv('TOKENS_PER_MIN', 60))
MAX_CHAT_HISTORY = int(os.getenv('MAX_CHAT_HISTORY', 10)) 