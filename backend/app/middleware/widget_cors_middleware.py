from fastapi import Request
from fastapi.responses import Response
import logging

logger = logging.getLogger(__name__)

async def widget_cors_middleware(request: Request, call_next):
    """Middleware مخصوص CORS برای widget API"""
    
    # اگر درخواست OPTIONS است، مستقیماً پاسخ CORS بده
    if request.method == "OPTIONS" and "/api/widget/" in request.url.path:
        response = Response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
        response.headers["Access-Control-Max-Age"] = "86400"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response
    
    # برای سایر درخواست‌ها، ادامه بده
    response = await call_next(request)
    
    # اضافه کردن CORS headers به همه پاسخ‌های widget API
    if "/api/widget/" in request.url.path:
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
        response.headers["Access-Control-Allow-Credentials"] = "true"
    
    return response
