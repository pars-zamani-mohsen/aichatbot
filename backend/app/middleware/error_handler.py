from fastapi import Request
from starlette.responses import JSONResponse
from ..core.logging_config import get_logger

logger = get_logger(__name__)

async def error_handler(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        logger.error(f"خطای ناشناخته: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": "خطای داخلی سرور"}
        ) 