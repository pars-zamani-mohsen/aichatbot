import time
import logging
from typing import Dict, Tuple
from collections import defaultdict, deque
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import threading

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate Limiter برای کنترل تعداد درخواست‌ها"""
    
    def __init__(self):
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.lock = threading.Lock()
        
        # تنظیمات Rate Limiting
        self.limits = {
            "chat": {"requests": 10, "window": 60},  # 10 چت در دقیقه
            "crawl": {"requests": 2, "window": 300},  # 2 کراول در 5 دقیقه
            "api": {"requests": 100, "window": 60},   # 100 درخواست API در دقیقه
            "widget": {"requests": 50, "window": 60}  # 50 درخواست widget در دقیقه
        }
    
    def is_allowed(self, key: str, limit_type: str = "api") -> Tuple[bool, Dict[str, int]]:
        """بررسی مجاز بودن درخواست"""
        current_time = time.time()
        limit_config = self.limits.get(limit_type, self.limits["api"])
        
        with self.lock:
            # پاکسازی درخواست‌های قدیمی
            while (self.requests[key] and 
                   current_time - self.requests[key][0] > limit_config["window"]):
                self.requests[key].popleft()
            
            # بررسی تعداد درخواست‌ها
            request_count = len(self.requests[key])
            is_allowed = request_count < limit_config["requests"]
            
            if is_allowed:
                self.requests[key].append(current_time)
            
            return is_allowed, {
                "remaining": max(0, limit_config["requests"] - request_count),
                "reset_time": current_time + limit_config["window"],
                "limit": limit_config["requests"]
            }
    
    def get_stats(self, key: str) -> Dict[str, int]:
        """دریافت آمار درخواست‌ها"""
        current_time = time.time()
        
        with self.lock:
            # پاکسازی درخواست‌های قدیمی
            while (self.requests[key] and 
                   current_time - self.requests[key][0] > 60):
                self.requests[key].popleft()
            
            return {
                "total_requests": len(self.requests[key]),
                "requests_last_minute": len([t for t in self.requests[key] 
                                           if current_time - t <= 60])
            }

# Instance سراسری
rate_limiter = RateLimiter()

async def rate_limit_middleware(request: Request, call_next):
    """Middleware برای Rate Limiting"""
    # تعیین نوع درخواست
    path = request.url.path
    if "/api/chats" in path:
        limit_type = "chat"
    elif "/api/websites/crawl" in path:
        limit_type = "crawl"
    elif "/api/widget" in path:
        limit_type = "widget"
    else:
        limit_type = "api"
    
    # دریافت کلید (IP یا User ID)
    client_ip = request.client.host
    user_id = getattr(request.state, "user_id", None)
    key = f"{user_id}_{client_ip}" if user_id else client_ip
    
    # بررسی Rate Limit
    is_allowed, limits = rate_limiter.is_allowed(key, limit_type)
    
    if not is_allowed:
        logger.warning(f"Rate limit exceeded for {key} ({limit_type})")
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "retry_after": int(limits["reset_time"] - time.time()),
                "limits": limits
            }
        )
    
    # اضافه کردن headers
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(limits["limit"])
    response.headers["X-RateLimit-Remaining"] = str(limits["remaining"])
    response.headers["X-RateLimit-Reset"] = str(int(limits["reset_time"]))
    
    return response
