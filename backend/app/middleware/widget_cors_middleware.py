from fastapi import Request, Response
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

async def widget_cors_middleware(request: Request, call_next):
    """Middleware سفارشی برای CORS ویجت"""
    
    # بررسی اینکه آیا درخواست مربوط به widget است
    if request.url.path.startswith("/api/widget/"):
        
        # Handle OPTIONS requests
        if request.method == "OPTIONS":
            return Response(
                status_code=200,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
                    "Access-Control-Max-Age": "86400",
                    "Content-Length": "0"
                }
            )
        
        # پردازش درخواست اصلی
        response = await call_next(request)
        
        # اضافه کردن CORS headers به response
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
        
        return response
    
    # برای سایر درخواست‌ها، بدون تغییر عبور دهید
    return await call_next(request)