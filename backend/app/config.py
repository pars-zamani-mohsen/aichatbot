# from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from dotenv import load_dotenv

# بارگذاری متغیرهای محیطی
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

class Settings:
    # تنظیمات شبکه مرکزی
    SERVER_IP = os.getenv("SERVER_IP", "localhost")
    
    # تنظیمات پورت‌ها
    BACKEND_PORT = os.getenv("BACKEND_PORT", "5000")
    FRONTEND_PORT = os.getenv("FRONTEND_PORT", "3001")
    DATABASE_PORT = os.getenv("DATABASE_PORT", "5432")
    REDIS_PORT = os.getenv("REDIS_PORT", "6379")
    CHROMA_PORT = os.getenv("CHROMA_PORT", "8000")
    
    # تنظیمات CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "")
    
    # تنظیمات دیتابیس
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "ai_user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "ai_password")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "ai_chatbot")
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
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "500"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))
    
    # تنظیمات جستجو
    COLLECTION_NAME: str = os.getenv("COLLECTION_NAME", "documents")
    KNOWLEDGE_BASE_DIR: str = os.getenv("KNOWLEDGE_BASE_DIR", "/app/knowledge_base")
    
    # تنظیمات CORS
    @property
    def CORS_ORIGINS_LIST(self) -> List[str]:
        """CORS origins بر اساس SERVER_IP و CORS_ORIGINS"""
        if not self.CORS_ORIGINS:
            # اگر CORS_ORIGINS تنظیم نشده، از SERVER_IP و پورت‌ها استفاده کن
            return [
                f"http://{self.SERVER_IP}:{self.FRONTEND_PORT}",
                f"http://{self.SERVER_IP}:3000",
                f"http://localhost:{self.FRONTEND_PORT}",
                "http://localhost:3000"
            ]
        
        # تبدیل string به list
        origins = [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        
        # در development، اگر origins خالی است، اجازه همه
        if self.DEBUG_MODE and not origins:
            return ["*"]
        
        return origins
    
    # تنظیمات API URL
    @property
    def API_BASE_URL(self) -> str:
        """API Base URL بر اساس SERVER_IP و BACKEND_PORT"""
        return os.getenv("API_BASE_URL", f"http://{self.SERVER_IP}:{self.BACKEND_PORT}")
    
    # تنظیمات Redis
    @property
    def REDIS_URL(self) -> str:
        """Redis URL بر اساس REDIS_PORT"""
        return os.getenv("REDIS_URL", f"redis://localhost:{self.REDIS_PORT}/0")
    
    # تنظیمات امنیتی
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    ALGORITHM: str = "HS256"
    
    # تنظیمات Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "200"))  # افزایش حد مجاز
    RATE_LIMIT_PER_HOUR: int = int(os.getenv("RATE_LIMIT_PER_HOUR", "1000"))
    RATE_LIMIT_CHAT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_CHAT_PER_MINUTE", "100"))  # افزایش حد مجاز
    RATE_LIMIT_CRAWL_PER_HOUR: int = int(os.getenv("RATE_LIMIT_CRAWL_PER_HOUR", "20"))  # افزایش حد مجاز
    RATE_LIMIT_WIDGET_PER_HOUR: int = int(os.getenv("RATE_LIMIT_WIDGET_PER_HOUR", "100"))  # افزایش حد مجاز
    
    # تنظیمات File Upload Security
    MAX_FILE_SIZE: str = os.getenv("MAX_FILE_SIZE", "50MB")
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
    @property
    def FRONTEND_URL(self) -> str:
        """Frontend URL بر اساس SERVER_IP و FRONTEND_PORT"""
        return os.getenv("FRONTEND_URL", f"http://{self.SERVER_IP}:{self.FRONTEND_PORT}")
    
    # تنظیمات لاگ
    @property
    def DEBUG_MODE(self) -> bool:
        """DEBUG mode from environment variable"""
        return os.getenv("DEBUG", "false").lower() == "true"
    
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(levelname)s - %(message)s"
    
    # class Config:
    #     case_sensitive = True
    #     extra = "ignore"  # نادیده گرفتن فیلدهای اضافی
    #     env_file = ".env"

settings = Settings() 