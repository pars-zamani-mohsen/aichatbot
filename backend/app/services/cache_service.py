"""
سرویس Cache برای بهبود عملکرد سیستم
"""

import json
import hashlib
from typing import Any, Optional, Union, Dict, List
from datetime import datetime, timedelta
import asyncio
from functools import wraps
import logging

logger = logging.getLogger(__name__)

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, using in-memory cache")

class CacheService:
    """سرویس Cache برای بهبود عملکرد"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", default_ttl: int = 3600):
        """
        مقداردهی اولیه سرویس cache
        
        Args:
            redis_url: آدرس Redis
            default_ttl: زمان انقضای پیش‌فرض (ثانیه)
        """
        self.default_ttl = default_ttl
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                self.redis_client.ping()
                self.use_redis = True
                logger.info("Redis cache initialized successfully")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}, using in-memory cache")
                self.use_redis = False
        else:
            self.use_redis = False
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """
        تولید کلید cache
        
        Args:
            prefix: پیشوند کلید
            *args: آرگومان‌های اضافی
            **kwargs: آرگومان‌های keyword
            
        Returns:
            کلید cache
        """
        # ترکیب آرگومان‌ها
        key_parts = [prefix]
        
        if args:
            key_parts.extend([str(arg) for arg in args])
        
        if kwargs:
            # مرتب کردن kwargs برای consistency
            sorted_kwargs = sorted(kwargs.items())
            key_parts.extend([f"{k}:{v}" for k, v in sorted_kwargs])
        
        key_string = "|".join(key_parts)
        
        # ایجاد hash برای کلیدهای طولانی
        if len(key_string) > 100:
            return f"{prefix}:{hashlib.md5(key_string.encode()).hexdigest()}"
        
        return key_string
    
    def get(self, key: str) -> Optional[Any]:
        """
        دریافت مقدار از cache
        
        Args:
            key: کلید cache
            
        Returns:
            مقدار cache شده یا None
        """
        try:
            if self.use_redis:
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value)
            else:
                cache_item = self._memory_cache.get(key)
                if cache_item and cache_item['expires_at'] > datetime.now():
                    return cache_item['value']
                elif cache_item:
                    # حذف آیتم منقضی شده
                    del self._memory_cache[key]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        ذخیره مقدار در cache
        
        Args:
            key: کلید cache
            value: مقدار برای ذخیره
            ttl: زمان انقضا (ثانیه)
            
        Returns:
            True در صورت موفقیت
        """
        try:
            ttl = ttl or self.default_ttl
            
            if self.use_redis:
                return self.redis_client.setex(key, ttl, json.dumps(value))
            else:
                expires_at = datetime.now() + timedelta(seconds=ttl)
                self._memory_cache[key] = {
                    'value': value,
                    'expires_at': expires_at
                }
                return True
                
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        حذف کلید از cache
        
        Args:
            key: کلید برای حذف
            
        Returns:
            True در صورت موفقیت
        """
        try:
            if self.use_redis:
                return bool(self.redis_client.delete(key))
            else:
                if key in self._memory_cache:
                    del self._memory_cache[key]
                return True
                
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """
        حذف کلیدها بر اساس pattern
        
        Args:
            pattern: الگوی کلیدها
            
        Returns:
            تعداد کلیدهای حذف شده
        """
        try:
            if self.use_redis:
                keys = self.redis_client.keys(pattern)
                if keys:
                    return self.redis_client.delete(*keys)
                return 0
            else:
                # برای memory cache، pattern matching ساده
                deleted_count = 0
                keys_to_delete = [k for k in self._memory_cache.keys() if pattern in k]
                for key in keys_to_delete:
                    del self._memory_cache[key]
                    deleted_count += 1
                return deleted_count
                
        except Exception as e:
            logger.error(f"Error deleting cache pattern {pattern}: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """
        بررسی وجود کلید در cache
        
        Args:
            key: کلید برای بررسی
            
        Returns:
            True اگر کلید وجود دارد
        """
        try:
            if self.use_redis:
                return bool(self.redis_client.exists(key))
            else:
                cache_item = self._memory_cache.get(key)
                return cache_item is not None and cache_item['expires_at'] > datetime.now()
                
        except Exception as e:
            logger.error(f"Error checking cache key {key}: {e}")
            return False
    
    def ttl(self, key: str) -> int:
        """
        دریافت زمان باقی‌مانده تا انقضا
        
        Args:
            key: کلید cache
            
        Returns:
            زمان باقی‌مانده (ثانیه) یا -1 اگر کلید وجود ندارد
        """
        try:
            if self.use_redis:
                return self.redis_client.ttl(key)
            else:
                cache_item = self._memory_cache.get(key)
                if cache_item:
                    remaining = (cache_item['expires_at'] - datetime.now()).total_seconds()
                    return max(0, int(remaining))
                return -1
                
        except Exception as e:
            logger.error(f"Error getting TTL for key {key}: {e}")
            return -1
    
    def clear(self) -> bool:
        """
        پاک کردن تمام cache
        
        Returns:
            True در صورت موفقیت
        """
        try:
            if self.use_redis:
                return bool(self.redis_client.flushdb())
            else:
                self._memory_cache.clear()
                return True
                
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        دریافت آمار cache
        
        Returns:
            دیکشنری آمار
        """
        try:
            if self.use_redis:
                info = self.redis_client.info()
                return {
                    'type': 'redis',
                    'connected_clients': info.get('connected_clients', 0),
                    'used_memory_human': info.get('used_memory_human', '0B'),
                    'keyspace_hits': info.get('keyspace_hits', 0),
                    'keyspace_misses': info.get('keyspace_misses', 0),
                    'total_commands_processed': info.get('total_commands_processed', 0)
                }
            else:
                # حذف آیتم‌های منقضی شده
                current_time = datetime.now()
                expired_keys = [
                    k for k, v in self._memory_cache.items() 
                    if v['expires_at'] <= current_time
                ]
                for key in expired_keys:
                    del self._memory_cache[key]
                
                return {
                    'type': 'memory',
                    'total_keys': len(self._memory_cache),
                    'memory_usage': 'N/A',
                    'expired_keys_cleaned': len(expired_keys)
                }
                
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {'error': str(e)}
    
    def memoize(self, ttl: Optional[int] = None, key_prefix: str = "memoize"):
        """
        Decorator برای cache کردن نتایج توابع
        
        Args:
            ttl: زمان انقضا (ثانیه)
            key_prefix: پیشوند کلید cache
            
        Returns:
            Decorator function
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # تولید کلید cache
                cache_key = self._generate_key(key_prefix, func.__name__, *args, **kwargs)
                
                # بررسی cache
                cached_result = self.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # اجرای تابع
                result = func(*args, **kwargs)
                
                # ذخیره در cache
                self.set(cache_key, result, ttl)
                
                return result
            
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # تولید کلید cache
                cache_key = self._generate_key(key_prefix, func.__name__, *args, **kwargs)
                
                # بررسی cache
                cached_result = self.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # اجرای تابع async
                result = await func(*args, **kwargs)
                
                # ذخیره در cache
                self.set(cache_key, result, ttl)
                
                return result
            
            # برگرداندن wrapper مناسب
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return wrapper
        
        return decorator
    
    def invalidate_by_pattern(self, pattern: str) -> int:
        """
        حذف cache بر اساس pattern (برای invalidation)
        
        Args:
            pattern: الگوی کلیدها
            
        Returns:
            تعداد کلیدهای حذف شده
        """
        return self.delete_pattern(pattern)
    
    def warm_up(self, warm_up_data: Dict[str, Any]) -> bool:
        """
        گرم کردن cache با داده‌های اولیه
        
        Args:
            warm_up_data: دیکشنری داده‌های اولیه
            
        Returns:
            True در صورت موفقیت
        """
        try:
            for key, value in warm_up_data.items():
                self.set(key, value)
            logger.info(f"Cache warmed up with {len(warm_up_data)} items")
            return True
        except Exception as e:
            logger.error(f"Error warming up cache: {e}")
            return False


# Instance سراسری
cache_service = CacheService()

# Decorator های آماده
memoize = cache_service.memoize
cache_get = cache_service.get
cache_set = cache_service.set
cache_delete = cache_service.delete
cache_exists = cache_service.exists
cache_clear = cache_service.clear
cache_stats = cache_service.get_stats
