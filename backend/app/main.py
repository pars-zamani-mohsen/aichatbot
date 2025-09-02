import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database.database import engine
from .database import models
from .api import websites, chats, auth, widget, dashboard, notifications, email_archive
from .config import settings
from .middleware import error_handler, logging_middleware
from .middleware.maintenance_middleware import maintenance_middleware
from .middleware.debug_middleware import debug_middleware
from .middleware.rate_limiter import rate_limit_middleware
from .services.crawler_queue import crawler_queue
from .core.logging_config import setup_logging
import logging

# تنظیم لاگینگ
setup_logging()
logger = logging.getLogger(__name__)

# ایجاد جداول دیتابیس
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="RAG Chatbot API",
    description="API برای چت‌بات مبتنی بر RAG",
    version="1.0.0"
)

# اضافه کردن میدلورها
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
app.middleware("http")(maintenance_middleware)
app.middleware("http")(debug_middleware)
app.middleware("http")(error_handler)
app.middleware("http")(logging_middleware)
app.middleware("http")(rate_limit_middleware)

# اضافه کردن روترها
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(websites.router, prefix="/api", tags=["websites"])
app.include_router(chats.router, prefix="/api/chats", tags=["chats"])
app.include_router(widget.router, prefix="/api/widget", tags=["widget"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])
app.include_router(email_archive.router, prefix="/api", tags=["email_archive"])

@app.get("/")
async def root():
    return {"message": "به API چت‌بات خوش آمدید"}

@app.on_event("startup")
async def startup_event():
    """شروع سیستم‌های مدیریت همزمانی"""
    crawler_queue.start()
    logger.info("Crawler queue started")

@app.on_event("shutdown")
async def shutdown_event():
    """توقف سیستم‌های مدیریت همزمانی"""
    crawler_queue.stop()
    logger.info("Crawler queue stopped") 