from fastapi import Request
from fastapi.responses import Response
import logging

logger = logging.getLogger(__name__)

async def security_middleware(request: Request, call_next):
    """Middleware برای اضافه کردن security headers"""
    
    response = await call_next(request)
    
    # Security Headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    # برای widget API، X-Frame-Options را کمتر محدودکننده کنیم
    if "/api/widget/" in request.url.path:
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
    else:
        response.headers["X-Frame-Options"] = "DENY"
    
    # HSTS (فقط برای HTTPS)
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    # Content Security Policy - برای widget API کمتر محدودکننده
    if "/api/widget/" in request.url.path:
        csp_policy = (
            "default-src 'self' *; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' *; "
            "style-src 'self' 'unsafe-inline' *; "
            "font-src 'self' *; "
            "img-src 'self' data: *; "
            "connect-src 'self' *; "
            "frame-ancestors *;"
        )
    else:
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://api.openai.com https://generativelanguage.googleapis.com; "
            "frame-ancestors 'none';"
        )
    response.headers["Content-Security-Policy"] = csp_policy
    
    return response
