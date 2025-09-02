from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session
from typing import Optional
import logging
from .system_settings_service import SystemSettingsService

logger = logging.getLogger(__name__)

class TimezoneManager:
    """مدیریت timezone سیستم با کش"""
    
    _cached_timezone = None
    _cached_zone_info = None
    
    @classmethod
    def get_system_timezone(cls, db: Session) -> str:
        """دریافت timezone سیستم از دیتابیس با کش"""
        if cls._cached_timezone is None:
            cls._cached_timezone = SystemSettingsService.get_system_timezone(db)
        return cls._cached_timezone
    
    @classmethod
    def get_system_zone_info(cls, db: Session) -> ZoneInfo:
        """دریافت ZoneInfo سیستم با کش"""
        if cls._cached_zone_info is None:
            timezone_str = cls.get_system_timezone(db)
            try:
                cls._cached_zone_info = ZoneInfo(timezone_str)
            except Exception as e:
                logger.error(f"Invalid timezone {timezone_str}: {str(e)}")
                cls._cached_zone_info = ZoneInfo("Asia/Tehran")
        return cls._cached_zone_info
    
    @classmethod
    def get_current_datetime(cls, db: Session) -> datetime:
        """دریافت datetime فعلی با timezone سیستم"""
        zone_info = cls.get_system_zone_info(db)
        return datetime.now(zone_info)
    
    @classmethod
    def get_current_date(cls, db: Session) -> datetime.date:
        """دریافت تاریخ فعلی با timezone سیستم"""
        return cls.get_current_datetime(db).date()
    
    @classmethod
    def convert_to_system_timezone(cls, dt: datetime, db: Session) -> datetime:
        """تبدیل datetime به timezone سیستم"""
        if dt.tzinfo is None:
            # اگر timezone ندارد، فرض کن UTC است
            dt = dt.replace(tzinfo=timezone.utc)
        
        system_zone = cls.get_system_zone_info(db)
        return dt.astimezone(system_zone)
    
    @classmethod
    def clear_cache(cls):
        """پاک کردن کش"""
        cls._cached_timezone = None
        cls._cached_zone_info = None
    
    @classmethod
    def update_system_timezone(cls, db: Session, new_timezone: str) -> bool:
        """به‌روزرسانی timezone سیستم"""
        try:
            # تست timezone
            ZoneInfo(new_timezone)
            
            # ذخیره در دیتابیس
            success = SystemSettingsService.set_setting(
                db, 
                'systemTimezone', 
                new_timezone, 
                'string', 
                'System timezone setting',
                'general'
            )
            
            if success:
                # پاک کردن کش
                cls.clear_cache()
                logger.info(f"System timezone updated to {new_timezone}")
                return True
            else:
                logger.error(f"Failed to update system timezone to {new_timezone}")
                return False
                
        except Exception as e:
            logger.error(f"Invalid timezone {new_timezone}: {str(e)}")
            return False
    
    @classmethod
    def get_available_timezones(cls) -> list:
        """دریافت لیست timezone های موجود"""
        return [
            "Asia/Tehran",
            "UTC",
            "Europe/London",
            "America/New_York",
            "Asia/Dubai",
            "Asia/Kolkata",
            "Asia/Shanghai",
            "Asia/Tokyo",
            "Europe/Paris",
            "Europe/Berlin",
            "America/Los_Angeles",
            "Australia/Sydney"
        ]
