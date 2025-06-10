from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from dotenv import load_dotenv

# بارگذاری متغیرهای محیطی
load_dotenv()

class Settings(BaseSettings):
    # تنظیمات دیتابیس
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "ai_user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "ai_password")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "ai_db")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    DATABASE_URL: str = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    
    # تنظیمات API
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_API_BASE_URL: str = os.getenv("OPENAI_API_BASE_URL", "")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    OLLAMA_API_URL: str = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
    
    # تنظیمات مدل
    EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    GEMINI_MODEL_NAME: str = os.getenv("GEMINI_MODEL_NAME", "gemini-pro")
    OPENAI_MODEL_NAME: str = os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo")
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "2000"))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))
    TOKENS_PER_MIN: int = int(os.getenv("TOKENS_PER_MIN", "60"))
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.5"))
    CHAT_HISTORY_LENGTH: int = int(os.getenv("CHAT_HISTORY_LENGTH", "5"))
    
    # تنظیمات کراولر
    MAX_PAGES: int = int(os.getenv("MAX_PAGES", "100"))
    MAX_DEPTH: int = int(os.getenv("MAX_DEPTH", "3"))
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))
    
    # تنظیمات جستجو
    COLLECTION_NAME: str = os.getenv("COLLECTION_NAME", "documents")
    KNOWLEDGE_BASE_DIR: str = os.getenv("KNOWLEDGE_BASE_DIR", "/var/www/html/ai/backend/knowledge_base")
    
    # تنظیمات CORS
    CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
    
    # تنظیمات Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # تنظیمات امنیتی
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))  # 7 days
    ALGORITHM: str = "HS256"
    
    # تنظیمات لاگ
    DEBUG_MODE: bool = False  # حالت دیباگ برای لاگ‌های دقیق
    LOG_LEVEL: str = "INFO"  # سطح لاگ پیش‌فرض
    LOG_FORMAT: str = "%(asctime)s - %(levelname)s - %(message)s"  # فرمت لاگ
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings() 