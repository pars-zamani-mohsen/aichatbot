"""
API endpoints برای نظارت بر عملکرد سیستم
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List
import logging

from app.services.performance_service import (
    performance_monitor,
    get_metrics_summary,
    clear_old_metrics
)
from app.services.cache_service import cache_service, cache_stats
from app.database.database import get_db
from app.api.auth import get_current_user
from app.database.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/performance", tags=["Performance"])


@router.get("/metrics/system")
async def get_system_metrics(
    hours: int = Query(24, description="تعداد ساعت برای محاسبه آمار"),
    current_user = Depends(get_current_user)
):
    """دریافت آمار عملکرد سیستم"""
    try:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="فقط ادمین می‌تواند آمار سیستم را ببیند")
        
        metrics = performance_monitor.get_metrics_summary('system', hours)
        return {
            "success": True,
            "data": metrics,
            "hours": hours
        }
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/database")
async def get_database_metrics(
    hours: int = Query(24, description="تعداد ساعت برای محاسبه آمار"),
    current_user = Depends(get_current_user)
):
    """دریافت آمار عملکرد دیتابیس"""
    try:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="فقط ادمین می‌تواند آمار دیتابیس را ببیند")
        
        metrics = performance_monitor.get_metrics_summary('database_queries', hours)
        return {
            "success": True,
            "data": metrics,
            "hours": hours
        }
    except Exception as e:
        logger.error(f"Error getting database metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/api")
async def get_api_metrics(
    hours: int = Query(24, description="تعداد ساعت برای محاسبه آمار"),
    current_user = Depends(get_current_user)
):
    """دریافت آمار عملکرد API"""
    try:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="فقط ادمین می‌تواند آمار API را ببیند")
        
        metrics = performance_monitor.get_metrics_summary('api_calls', hours)
        return {
            "success": True,
            "data": metrics,
            "hours": hours
        }
    except Exception as e:
        logger.error(f"Error getting API metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/cache")
async def get_cache_metrics(
    hours: int = Query(24, description="تعداد ساعت برای محاسبه آمار"),
    current_user = Depends(get_current_user)
):
    """دریافت آمار عملکرد cache"""
    try:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="فقط ادمین می‌تواند آمار cache را ببیند")
        
        metrics = performance_monitor.get_metrics_summary('cache_operations', hours)
        cache_info = cache_stats()
        
        return {
            "success": True,
            "data": {
                "metrics": metrics,
                "cache_info": cache_info
            },
            "hours": hours
        }
    except Exception as e:
        logger.error(f"Error getting cache metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts")
async def get_performance_alerts(
    current_user = Depends(get_current_user)
):
    """دریافت هشدارهای عملکرد"""
    try:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="فقط ادمین می‌تواند هشدارها را ببیند")
        
        alerts = performance_monitor.get_performance_alerts()
        return {
            "success": True,
            "data": alerts,
            "count": len(alerts)
        }
    except Exception as e:
        logger.error(f"Error getting performance alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/clear")
async def clear_cache(
    pattern: str = Query("*", description="الگوی کلیدهای cache برای حذف"),
    current_user = Depends(get_current_user)
):
    """پاکسازی cache"""
    try:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="فقط ادمین می‌تواند cache را پاک کند")
        
        deleted_count = cache_service.invalidate_by_pattern(pattern)
        
        return {
            "success": True,
            "message": f"{deleted_count} کلید cache حذف شد",
            "deleted_count": deleted_count,
            "pattern": pattern
        }
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/warm-up")
async def warm_up_cache(
    current_user = Depends(get_current_user)
):
    """گرم کردن cache با داده‌های اولیه"""
    try:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="فقط ادمین می‌تواند cache را گرم کند")
        
        # داده‌های اولیه برای cache
        warm_up_data = {
            "system_settings": {},
            "user_count": 0,
            "website_count": 0
        }
        
        # دریافت آمار اولیه
        db = next(get_db())
        try:
            from app.models import User, Website
            warm_up_data["user_count"] = db.query(User).count()
            warm_up_data["website_count"] = db.query(Website).count()
        finally:
            db.close()
        
        # گرم کردن cache
        success = cache_service.warm_up(warm_up_data)
        
        if success:
            return {
                "success": True,
                "message": "Cache با موفقیت گرم شد",
                "data": warm_up_data
            }
        else:
            raise HTTPException(status_code=500, detail="خطا در گرم کردن cache")
            
    except Exception as e:
        logger.error(f"Error warming up cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/metrics/clear")
async def clear_old_metrics_endpoint(
    days: int = Query(7, description="تعداد روزهای نگهداری metrics"),
    current_user = Depends(get_current_user)
):
    """پاکسازی metrics قدیمی"""
    try:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="فقط ادمین می‌تواند metrics را پاک کند")
        
        clear_old_metrics(days)
        
        return {
            "success": True,
            "message": f"Metrics قدیمی‌تر از {days} روز پاک شدند",
            "days": days
        }
    except Exception as e:
        logger.error(f"Error clearing old metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def get_system_health(
    current_user = Depends(get_current_user)
):
    """دریافت وضعیت سلامت سیستم"""
    try:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="فقط ادمین می‌تواند وضعیت سلامت را ببیند")
        
        # بررسی آمار سیستم
        system_metrics = get_metrics_summary('system', hours=1)
        
        # بررسی هشدارها
        alerts = performance_monitor.get_performance_alerts()
        
        # تعیین وضعیت کلی
        health_status = "healthy"
        if alerts:
            critical_alerts = [a for a in alerts if a['severity'] == 'critical']
            if critical_alerts:
                health_status = "critical"
            else:
                health_status = "warning"
        
        # بررسی cache
        cache_info = cache_stats()
        
        return {
            "success": True,
            "data": {
                "status": health_status,
                "system": system_metrics,
                "alerts": alerts,
                "cache": cache_info,
                "timestamp": performance_monitor.metrics['system'][-1]['timestamp'] if performance_monitor.metrics['system'] else None
            }
        }
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_performance_summary(
    current_user = Depends(get_current_user)
):
    """دریافت خلاصه عملکرد سیستم"""
    try:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="فقط ادمین می‌تواند خلاصه عملکرد را ببیند")
        
        # آمار 24 ساعته
        system_24h = get_metrics_summary('system', 24)
        db_24h = get_metrics_summary('database_queries', 24)
        api_24h = get_metrics_summary('api_calls', 24)
        cache_24h = get_metrics_summary('cache_operations', 24)
        
        # آمار 1 ساعته
        system_1h = get_metrics_summary('system', 1)
        db_1h = get_metrics_summary('database_queries', 1)
        api_1h = get_metrics_summary('api_calls', 1)
        
        summary = {
            "24h": {
                "system": system_24h,
                "database": db_24h,
                "api": api_24h,
                "cache": cache_24h
            },
            "1h": {
                "system": system_1h,
                "database": db_1h,
                "api": api_1h
            },
            "alerts": performance_monitor.get_performance_alerts(),
            "cache_info": cache_stats()
        }
        
        return {
            "success": True,
            "data": summary
        }
    except Exception as e:
        logger.error(f"Error getting performance summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
