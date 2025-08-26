import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database.database import engine
from .database import models
from .api import websites, chats, auth, widget, dashboard
from .config import settings
from .middleware import error_handler, logging_middleware
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
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
app.middleware("http")(error_handler)
app.middleware("http")(logging_middleware)

# اضافه کردن روترها
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(websites.router, prefix="/api", tags=["websites"])
app.include_router(chats.router, prefix="/api/chats", tags=["chats"])
app.include_router(widget.router, prefix="/api/widget", tags=["widget"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])

@app.get("/")
async def root():
    return {"message": "به API چت‌بات خوش آمدید"} 