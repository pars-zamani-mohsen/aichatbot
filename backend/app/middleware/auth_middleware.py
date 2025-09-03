"""
Middleware برای مدیریت احراز هویت و بررسی token
"""
import logging
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from ..config import settings
from ..database.database import get_db
from ..database import models

logger = logging.getLogger(__name__)

async def auth_middleware(request: Request, call_next):
    """
    Middleware برای بررسی token در همه درخواست‌های API
    """
    # مسیرهایی که نیاز به احراز هویت ندارند
    public_paths = [
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/token",
        "/api/register",
        "/api/verify-email",
        "/api/reset-password",
        "/api/forgot-password",
        "/",
        "/health",
        "/favicon.ico"
    ]
    
    # بررسی مسیرهای عمومی
    if any(request.url.path.startswith(path) for path in public_paths):
        return await call_next(request)
    
    # بررسی مسیرهای API
    if request.url.path.startswith("/api/"):
        # بررسی وجود Authorization header
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            logger.warning(f"Missing Authorization header for path: {request.url.path}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": "هدر Authorization ارائه نشده است",
                    "code": "MISSING_AUTH_HEADER"
                },
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # بررسی فرمت Bearer token
        if not auth_header.startswith("Bearer "):
            logger.warning(f"Invalid Authorization header format for path: {request.url.path}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": "فرمت هدر Authorization نامعتبر است",
                    "code": "INVALID_AUTH_FORMAT"
                },
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # استخراج token
        token = auth_header.replace("Bearer ", "")
        
        if not token:
            logger.warning(f"Empty token for path: {request.url.path}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": "Token خالی است",
                    "code": "EMPTY_TOKEN"
                },
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # بررسی طول token
        if len(token) < 10:
            logger.warning(f"Token too short for path: {request.url.path}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": "Token خیلی کوتاه است",
                    "code": "TOKEN_TOO_SHORT"
                },
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # بررسی اعتبار JWT token
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            
            # بررسی وجود email در payload
            email = payload.get("sub")
            if not email:
                logger.warning(f"Token missing 'sub' field for path: {request.url.path}")
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "detail": "Token فاقد اطلاعات کاربر است",
                        "code": "MISSING_USER_INFO"
                    },
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # بررسی زمان انقضا
            exp = payload.get("exp")
            if exp:
                from datetime import datetime, timezone
                if datetime.now(timezone.utc).timestamp() > exp:
                    logger.warning(f"Token expired for path: {request.url.path}, user: {email}")
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={
                            "detail": "Token منقضی شده است",
                            "code": "TOKEN_EXPIRED"
                        },
                        headers={"WWW-Authenticate": "Bearer"}
                    )
            
            # اضافه کردن اطلاعات کاربر به request state
            request.state.user_email = email
            request.state.token_payload = payload
            
            logger.debug(f"Token validated successfully for path: {request.url.path}, user: {email}")
            
        except jwt.ExpiredSignatureError:
            logger.warning(f"Token expired (JWT error) for path: {request.url.path}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": "Token منقضی شده است",
                    "code": "TOKEN_EXPIRED"
                },
                headers={"WWW-Authenticate": "Bearer"}
            )
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token for path: {request.url.path}: {e}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": "Token نامعتبر است",
                    "code": "INVALID_TOKEN"
                },
                headers={"WWW-Authenticate": "Bearer"}
            )
        except Exception as e:
            logger.error(f"Unexpected error validating token for path: {request.url.path}: {e}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": "خطا در بررسی token",
                    "code": "TOKEN_VALIDATION_ERROR"
                },
                headers={"WWW-Authenticate": "Bearer"}
            )
    
    # ادامه درخواست
    response = await call_next(request)
    return response
