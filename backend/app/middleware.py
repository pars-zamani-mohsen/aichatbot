from fastapi import Request
from fastapi.responses import JSONResponse
import time
import logging
from .utils.exceptions import ChatbotError

logger = logging.getLogger(__name__)

async def error_handler(request: Request, call_next):
    """مدیریت خطاها"""
    try:
        return await call_next(request)
    except ChatbotError as e:
        logger.error(f"خطای چت‌بات: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)}
        )
    except Exception as e:
        logger.error(f"خطای ناشناخته: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": "خطای داخلی سرور"}
        )

async def logging_middleware(request: Request, call_next):
    """ثبت لاگ درخواست‌ها"""
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(
        f"Method: {request.method} Path: {request.url.path} "
        f"Status: {response.status_code} Duration: {process_time:.2f}s"
    )
    
    return response 