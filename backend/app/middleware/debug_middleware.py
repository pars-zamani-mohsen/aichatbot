from fastapi import Request
from sqlalchemy.orm import Session
from ..database.database import get_db
from ..services.system_settings_service import SystemSettingsService
import logging
import time

logger = logging.getLogger(__name__)

async def debug_middleware(request: Request, call_next):
    """Middleware برای debug mode"""
    
    try:
        # دریافت تنظیمات از دیتابیس
        db = next(get_db())
        debug_mode = SystemSettingsService.get_setting(db, 'debugMode', False)
        
        if debug_mode:
            # شروع زمان‌سنج
            start_time = time.time()
            
            # لاگ کردن درخواست
            logger.debug(f"DEBUG: {request.method} {request.url.path} - Headers: {dict(request.headers)}")
            
            # پردازش درخواست
            response = await call_next(request)
            
            # محاسبه زمان پردازش
            process_time = time.time() - start_time
            
            # لاگ کردن پاسخ
            logger.debug(f"DEBUG: {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.3f}s")
            
            # اضافه کردن header های debug
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Debug-Mode"] = "true"
            
            return response
        
    except Exception as e:
        logger.error(f"Error in debug middleware: {str(e)}")
    
    # اگر debug mode فعال نیست یا خطا رخ داده، ادامه عادی
    return await call_next(request)
