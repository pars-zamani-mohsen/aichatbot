import os
from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from .database.database import engine
from .database import models
from .api import websites, chats, auth, widget, dashboard, notifications, email_archive, performance
from .config import settings
from .middleware import error_handler, logging_middleware
from .middleware.maintenance_middleware import maintenance_middleware
from .middleware.debug_middleware import debug_middleware
from .middleware.rate_limiter import rate_limit_middleware
# from .middleware.security_middleware import security_middleware  # موقتاً غیرفعال
from .middleware.auth_middleware import auth_middleware
from .middleware.widget_cors_middleware import widget_cors_middleware
from .middleware.options_middleware import options_middleware
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

# بهبود CORS Configuration
import os
from .config import settings

# استفاده از تنظیمات از config.py
server_ip = settings.SERVER_IP
frontend_port = settings.FRONTEND_PORT
backend_port = settings.BACKEND_PORT

# CORS origins بر اساس IP اصلی
cors_origins = [
    f'http://{server_ip}:{frontend_port}',
    f'http://{server_ip}:3000',
    f'http://localhost:{frontend_port}',
    'http://localhost:3000',
    f'http://{server_ip}:{backend_port}',  # اضافه کردن backend port
    'http://localhost:5000',  # برای development
    '*'  # موقتاً برای تست
]

print(f"🌐 CORS Origins: {cors_origins}")
print(f"🔧 Server IP: {server_ip}")
print(f"🔧 Frontend Port: {frontend_port}")
print(f"🔧 Backend Port: {backend_port}")

# CORS Middleware سفارشی
from fastapi import Request
from fastapi.responses import Response

# اضافه کردن میدلورها - OPTIONS middleware موقتاً غیرفعال
# app.middleware("http")(options_middleware)

# CORS Middleware - FastAPI مسئول CORS است
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)
# سایر middleware ها موقتاً غیرفعال
# app.middleware("http")(logging_middleware)
# app.middleware("http")(error_handler)
# app.middleware("http")(debug_middleware)
# app.middleware("http")(maintenance_middleware)
# app.middleware("http")(auth_middleware)
# app.middleware("http")(rate_limit_middleware)
# app.middleware("http")(security_middleware)

# OPTIONS handlers توسط middleware handle می‌شوند

# اضافه کردن روترها
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(websites.router, prefix="/api", tags=["websites"])
app.include_router(chats.router, prefix="/api/chats", tags=["chats"])
app.include_router(widget.router, prefix="/api/widget", tags=["widget"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])
app.include_router(email_archive.router, prefix="/api", tags=["email_archive"])
app.include_router(performance.router, prefix="/api", tags=["performance"])

# OPTIONS handlers حذف شدند - از middleware استفاده می‌کنیم

@app.get("/")
async def root():
    return {"message": "به API چت‌بات خوش آمدید"}

@app.on_event("startup")
async def startup_event():
    """رویداد شروع برنامه"""
    logger.info("🚀 شروع برنامه...")
    # شروع crawler queue
    crawler_queue.start()

@app.on_event("shutdown")
async def shutdown_event():
    """رویداد پایان برنامه"""
    logger.info("🛑 پایان برنامه...")
    # توقف crawler queue
    crawler_queue.stop() # Test comment
