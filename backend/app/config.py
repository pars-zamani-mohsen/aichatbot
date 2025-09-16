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
    @property
    def CORS_ORIGINS(self) -> List[str]:
        """CORS origins بر اساس محیط"""
        cors_origins = os.getenv("CORS_ORIGINS", "")
        
        if not cors_origins:
            # اگر CORS_ORIGINS تنظیم نشده، بر اساس محیط تصمیم‌گیری
            if self.DEBUG_MODE:
                # Development: اجازه همه origins
                return ["*"]
            else:
                # Production: فقط origins مشخص شده
                return []
        
        # تبدیل string به list
        origins = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]
        
        # در development، اگر origins خالی است، اجازه همه
        if self.DEBUG_MODE and not origins:
            return ["*"]
        
        return origins
    
    # تنظیمات API URL
    API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:5000")
    
    # تنظیمات Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # تنظیمات امنیتی
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    ALGORITHM: str = "HS256"
    
    # تنظیمات Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    RATE_LIMIT_PER_HOUR: int = int(os.getenv("RATE_LIMIT_PER_HOUR", "1000"))
    RATE_LIMIT_CHAT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_CHAT_PER_MINUTE", "10"))
    RATE_LIMIT_CRAWL_PER_HOUR: int = int(os.getenv("RATE_LIMIT_CRAWL_PER_HOUR", "10"))
    RATE_LIMIT_WIDGET_PER_HOUR: int = int(os.getenv("RATE_LIMIT_WIDGET_PER_HOUR", "50"))
    
    # تنظیمات File Upload Security
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    
    @property
    def ALLOWED_FILE_TYPES(self) -> List[str]:
        """Allowed file types from environment variable"""
        file_types = os.getenv("ALLOWED_FILE_TYPES", "jpg,jpeg,png,pdf,txt,doc,docx")
        return [ft.strip() for ft in file_types.split(",") if ft.strip()]
    
    MAX_FILENAME_LENGTH: int = int(os.getenv("MAX_FILENAME_LENGTH", "100"))
    
    # تنظیمات Input Validation
    MAX_INPUT_LENGTH: int = int(os.getenv("MAX_INPUT_LENGTH", "1000"))
    MAX_MESSAGE_LENGTH: int = int(os.getenv("MAX_MESSAGE_LENGTH", "500"))
    MAX_URL_LENGTH: int = int(os.getenv("MAX_URL_LENGTH", "2048"))
    
    # تنظیمات Security Headers
    ENABLE_HSTS: bool = os.getenv("ENABLE_HSTS", "true").lower() == "true"
    ENABLE_CSP: bool = os.getenv("ENABLE_CSP", "true").lower() == "true"
    ENABLE_XSS_PROTECTION: bool = os.getenv("ENABLE_XSS_PROTECTION", "true").lower() == "true"
    
    # تنظیمات Session Security
    SESSION_TIMEOUT_MINUTES: int = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))
    MAX_LOGIN_ATTEMPTS: int = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
    LOGIN_LOCKOUT_MINUTES: int = int(os.getenv("LOGIN_LOCKOUT_MINUTES", "30"))
    PASSWORD_MIN_LENGTH: int = int(os.getenv("PASSWORD_MIN_LENGTH", "8"))
    REQUIRE_EMAIL_VERIFICATION: bool = os.getenv("REQUIRE_EMAIL_VERIFICATION", "true").lower() == "true"
    ENABLE_TWO_FACTOR: bool = os.getenv("ENABLE_TWO_FACTOR", "false").lower() == "true"
    
    # تنظیمات SMTP برای ایمیل
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    
    # تنظیمات فرانت‌اند
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # تنظیمات لاگ
    @property
    def DEBUG_MODE(self) -> bool:
        """DEBUG mode from environment variable"""
        return os.getenv("DEBUG", "false").lower() == "true"
    
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # نادیده گرفتن فیلدهای اضافی

settings = Settings() 