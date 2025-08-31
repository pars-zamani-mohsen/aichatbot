from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from ..database.database import get_db
from ..services.system_settings_service import SystemSettingsService
import logging

logger = logging.getLogger(__name__)

async def maintenance_middleware(request: Request, call_next):
    """Middleware برای بررسی حالت نگهداری"""
    
    # مسیرهایی که در حالت نگهداری هم قابل دسترسی هستند
    maintenance_allowed_paths = [
        "/admin/settings",  # ادمین باید بتواند تنظیمات را تغییر دهد
        "/api/dashboard/admin/system-settings",
        "/api/dashboard/admin/system-settings/",
        "/docs",  # مستندات API
        "/openapi.json"
    ]
    
    # درخواست‌های OPTIONS همیشه مجاز هستند (برای CORS)
    if request.method == "OPTIONS":
        return await call_next(request)
    
    # بررسی مسیرهای مجاز
    if any(request.url.path.startswith(path) for path in maintenance_allowed_paths):
        return await call_next(request)
    
    try:
        # دریافت تنظیمات از دیتابیس
        db = next(get_db())
        try:
            maintenance_mode = SystemSettingsService.get_setting(db, 'maintenanceMode', False)
            
            if maintenance_mode:
                # اگر در حالت نگهداری هستیم
                return JSONResponse(
                    status_code=503,
                    content={
                        "detail": "سیستم در حال نگهداری است. لطفاً بعداً تلاش کنید.",
                        "maintenance": True
                    }
                )
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"Error checking maintenance mode: {str(e)}")
        # در صورت خطا، اجازه ادامه می‌دهیم
    
    response = await call_next(request)
    return response
