from fastapi import Request, Response
import logging

logger = logging.getLogger(__name__)

async def options_middleware(request: Request, call_next):
    """Middleware برای handle کردن OPTIONS requests"""
    
    # اگر درخواست OPTIONS است، مستقیماً response برگردان
    if request.method == "OPTIONS":
        return Response(
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
                "Access-Control-Max-Age": "86400"
            }
        )
    
    # برای سایر درخواست‌ها، ادامه دهید
    response = await call_next(request)
    
    # اضافه کردن CORS headers به response
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
    
    return response
