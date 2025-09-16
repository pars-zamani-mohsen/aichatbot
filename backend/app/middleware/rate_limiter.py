import time
import logging
from typing import Dict, Tuple
from collections import defaultdict, deque
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import threading
from ..services.system_settings_service import SystemSettingsService

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate Limiter برای کنترل تعداد درخواست‌ها"""
    
    def __init__(self):
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.lock = threading.Lock()
        self._limits = None
        self._last_update = 0
        self._update_interval = 60  # به‌روزرسانی هر 60 ثانیه
        
    def _get_limits(self, db=None):
        """دریافت تنظیمات rate limiting از دیتابیس"""
        current_time = time.time()
        
        # اگر تنظیمات قدیمی هستند یا وجود ندارند، به‌روزرسانی کن
        if (self._limits is None or 
            current_time - self._last_update > self._update_interval):
            
            try:
                if db:
                    self._limits = SystemSettingsService.get_rate_limit_settings(db)
                else:
                    # مقادیر پیش‌فرض اگر دیتابیس در دسترس نباشد
                    self._limits = {
                        "chat": {"requests": 20, "window": 60},
                        "crawl": {"requests": 5, "window": 300},
                        "api": {"requests": 100, "window": 60},
                        "widget": {"requests": 50, "window": 60}
                    }
                self._last_update = current_time
            except Exception as e:
                logger.error(f"Error getting rate limit settings: {str(e)}")
                # استفاده از مقادیر پیش‌فرض
                self._limits = {
                    "chat": {"requests": 20, "window": 60},
                    "crawl": {"requests": 5, "window": 300},
                    "api": {"requests": 100, "window": 60},
                    "widget": {"requests": 50, "window": 60}
                }
        
        return self._limits
    
    def is_allowed(self, key: str, limit_type: str = "api", db=None) -> Tuple[bool, Dict[str, int]]:
        """بررسی مجاز بودن درخواست"""
        current_time = time.time()
        limits = self._get_limits(db)
        limit_config = limits.get(limit_type, limits["api"])
        
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
    
    def reset_limits(self, key: str = None):
        """ریست کردن محدودیت‌ها برای یک کلید خاص یا همه"""
        with self.lock:
            if key:
                if key in self.requests:
                    self.requests[key].clear()
                    logger.info(f"Rate limits reset for {key}")
            else:
                self.requests.clear()
                logger.info("All rate limits reset")

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
    
    # دریافت db session برای خواندن تنظیمات
    db = None
    try:
        from ..database.database import get_db
        db = next(get_db())
    except:
        pass
    
    # بررسی Rate Limit
    is_allowed, limits = rate_limiter.is_allowed(key, limit_type, db)
    
    if not is_allowed:
        logger.warning(f"Rate limit exceeded for {key} ({limit_type})")
        response = JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "detail": "تعداد درخواست‌ها بیش از حد مجاز است. لطفاً چند دقیقه صبر کنید و دوباره تلاش کنید.",
                "retry_after": int(limits["reset_time"] - time.time()),
                "limits": limits
            }
        )
        
        # اضافه کردن CORS headers
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        
        return response
    
    # اضافه کردن headers به response
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(limits["limit"])
    response.headers["X-RateLimit-Remaining"] = str(limits["remaining"])
    response.headers["X-RateLimit-Reset"] = str(int(limits["reset_time"]))
    
    return response
