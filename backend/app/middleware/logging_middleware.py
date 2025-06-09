import time
from fastapi import Request
from starlette.responses import Response
from ..core.logging_config import get_logger

logger = get_logger(__name__)

async def logging_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(
        f"Method: {request.method} "
        f"Path: {request.url.path} "
        f"Status: {response.status_code} "
        f"Duration: {process_time:.2f}s"
    )
    
    return response 