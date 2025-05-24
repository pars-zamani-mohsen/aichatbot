from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database.database import engine
from .database import models
from .api import websites, chats, auth
from .config import settings
from .middleware import error_handler, logging_middleware
import logging

# تنظیمات لاگینگ
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ایجاد جداول دیتابیس
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="RAG Chatbot API",
    description="API برای چت‌بات مبتنی بر RAG",
    version="1.0.0"
)

# تنظیمات CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# اضافه کردن میدلورها
app.middleware("http")(error_handler)
app.middleware("http")(logging_middleware)

# اضافه کردن روترها
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(websites.router, prefix="/api", tags=["websites"])
app.include_router(chats.router, prefix="/api", tags=["chats"])

@app.get("/")
async def root():
    return {"message": "به API چت‌بات خوش آمدید"} 