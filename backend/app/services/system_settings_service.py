from sqlalchemy.orm import Session
from ..database import models
from typing import Dict, Any, Optional
import json
import logging

logger = logging.getLogger(__name__)

class SystemSettingsService:
    """سرویس مدیریت تنظیمات سیستم"""
    
    _cache = {}
    _cache_loaded = False
    
    @classmethod
    def get_setting(cls, db: Session, key: str, default: Any = None) -> Any:
        """دریافت یک تنظیم خاص"""
        try:
            # ابتدا از کش بررسی کن
            if cls._cache_loaded and key in cls._cache:
                return cls._cache[key]
            
            # از دیتابیس بخوان
            setting = db.query(models.SystemSettings).filter(models.SystemSettings.key == key).first()
            
            if not setting:
                return default
            
            # تبدیل نوع داده
            value = cls._convert_value(setting.value, setting.value_type)
            
            # در کش ذخیره کن
            cls._cache[key] = value
            
            return value
            
        except Exception as e:
            logger.error(f"Error getting setting {key}: {str(e)}")
            return default
    
    @classmethod
    def get_all_settings(cls, db: Session) -> Dict[str, Any]:
        """دریافت تمام تنظیمات"""
        try:
            settings = db.query(models.SystemSettings).all()
            result = {}
            
            for setting in settings:
                result[setting.key] = cls._convert_value(setting.value, setting.value_type)
            
            # کش را به‌روزرسانی کن
            cls._cache = result
            cls._cache_loaded = True
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting all settings: {str(e)}")
            return {}
    
    @classmethod
    def set_setting(cls, db: Session, key: str, value: Any, value_type: str = None, description: str = None, category: str = "general") -> bool:
        """تنظیم یک مقدار خاص"""
        try:
            # تعیین نوع داده اگر مشخص نشده
            if value_type is None:
                value_type = cls._detect_value_type(value)
            
            # تبدیل به string برای ذخیره
            value_str = cls._convert_to_string(value)
            
            # بررسی وجود تنظیم
            existing = db.query(models.SystemSettings).filter(models.SystemSettings.key == key).first()
            
            if existing:
                # به‌روزرسانی
                existing.value = value_str
                existing.value_type = value_type
                if description:
                    existing.description = description
                if category:
                    existing.category = category
            else:
                # ایجاد جدید
                new_setting = models.SystemSettings(
                    key=key,
                    value=value_str,
                    value_type=value_type,
                    description=description or f"تنظیم {key}",
                    category=category
                )
                db.add(new_setting)
            
            db.commit()
            
            # کش را به‌روزرسانی کن
            cls._cache[key] = value
            cls._cache_loaded = True
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting {key}: {str(e)}")
            return False
    
    @classmethod
    def clear_cache(cls):
        """پاک کردن کش"""
        cls._cache = {}
        cls._cache_loaded = False
    
    @classmethod
    def _convert_value(cls, value: str, value_type: str) -> Any:
        """تبدیل مقدار string به نوع داده مناسب"""
        if not value:
            return None
            
        try:
            if value_type == 'integer':
                return int(value)
            elif value_type == 'float':
                return float(value)
            elif value_type == 'boolean':
                return value.lower() == 'true'
            elif value_type == 'json':
                return json.loads(value)
            else:
                return value
        except Exception as e:
            logger.error(f"Error converting value {value} to type {value_type}: {str(e)}")
            return value
    
    @classmethod
    def _convert_to_string(cls, value: Any) -> str:
        """تبدیل مقدار به string برای ذخیره"""
        if value is None:
            return ''
        elif isinstance(value, (list, dict)):
            return json.dumps(value, ensure_ascii=False)
        else:
            return str(value)
    
    @classmethod
    def _detect_value_type(cls, value: Any) -> str:
        """تشخیص نوع داده"""
        if isinstance(value, bool):
            return 'boolean'
        elif isinstance(value, int):
            return 'integer'
        elif isinstance(value, float):
            return 'float'
        elif isinstance(value, (list, dict)):
            return 'json'
        else:
            return 'string'
    
    @classmethod
    def get_email_settings(cls, db: Session) -> Dict[str, Any]:
        """دریافت تنظیمات ایمیل"""
        return {
            'smtp_server': cls.get_setting(db, 'smtpServer', 'smtp.gmail.com'),
            'smtp_port': cls.get_setting(db, 'smtpPort', 587),
            'smtp_username': cls.get_setting(db, 'smtpUsername', ''),
            'smtp_password': cls.get_setting(db, 'smtpPassword', ''),
            'email_from': cls.get_setting(db, 'emailFrom', ''),
        }
    
    @classmethod
    def get_security_settings(cls, db: Session) -> Dict[str, Any]:
        """دریافت تنظیمات امنیت"""
        return {
            'sessionTimeout': cls.get_setting(db, 'sessionTimeout', 30),
            'maxLoginAttempts': cls.get_setting(db, 'maxLoginAttempts', 5),
            'passwordMinLength': cls.get_setting(db, 'passwordMinLength', 8),
            'requireEmailVerification': cls.get_setting(db, 'requireEmailVerification', True),
            'enableTwoFactor': cls.get_setting(db, 'enableTwoFactor', False),
        }
    
    @classmethod
    def get_rag_settings(cls, db: Session) -> Dict[str, Any]:
        """دریافت تنظیمات RAG"""
        return {
            'defaultK': cls.get_setting(db, 'defaultK', 5),
            'maxResponseLength': cls.get_setting(db, 'maxResponseLength', 500),
            'defaultTemperature': cls.get_setting(db, 'defaultTemperature', 0.7),
            'defaultLanguage': cls.get_setting(db, 'defaultLanguage', 'fa'),
        }
    
    @classmethod
    def get_crawler_settings(cls, db: Session) -> Dict[str, Any]:
        """دریافت تنظیمات کراولر"""
        return {
            'maxPagesPerSite': cls.get_setting(db, 'maxPagesPerSite', 100),
            'crawlDelay': cls.get_setting(db, 'crawlDelay', 1),
            'respectRobotsTxt': cls.get_setting(db, 'respectRobotsTxt', True),
            'userAgent': cls.get_setting(db, 'userAgent', 'RAG-Chatbot-Crawler/1.0'),
        }
    
    @classmethod
    def get_notification_settings(cls, db: Session) -> Dict[str, Any]:
        """دریافت تنظیمات اعلان‌ها"""
        return {
            'email_notifications': cls.get_setting(db, 'emailNotifications', True),
            'slack_notifications': cls.get_setting(db, 'slackNotifications', False),
            'slack_webhook': cls.get_setting(db, 'slackWebhook', ''),
            'notify_on_error': cls.get_setting(db, 'notifyOnError', True),
            'notify_on_new_user': cls.get_setting(db, 'notifyOnNewUser', True),
        }
    
    @classmethod
    def get_timezone_settings(cls, db: Session) -> Dict[str, Any]:
        """دریافت تنظیمات timezone"""
        return {
            'system_timezone': cls.get_setting(db, 'systemTimezone', 'Asia/Tehran'),
            'default_timezone': cls.get_setting(db, 'defaultTimezone', 'Asia/Tehran'),
            'timezone_format': cls.get_setting(db, 'timezoneFormat', 'Asia/Tehran'),
        }
    
    @classmethod
    def get_system_timezone(cls, db: Session) -> str:
        """دریافت timezone سیستم با کش"""
        return cls.get_setting(db, 'systemTimezone', 'Asia/Tehran')
    
    @classmethod
    def get_rate_limit_settings(cls, db: Session) -> Dict[str, Dict[str, int]]:
        """دریافت تنظیمات rate limiting"""
        try:
            return {
                "chat": {
                    "requests": int(cls.get_setting(db, "rate_limit_chat_requests", 100)),  # افزایش از 20 به 100
                    "window": int(cls.get_setting(db, "rate_limit_chat_window", 60))
                },
                "crawl": {
                    "requests": int(cls.get_setting(db, "rate_limit_crawl_requests", 10)),  # افزایش از 5 به 10
                    "window": int(cls.get_setting(db, "rate_limit_crawl_window", 300))
                },
                "api": {
                    "requests": int(cls.get_setting(db, "rate_limit_api_requests", 200)),  # افزایش از 100 به 200
                    "window": int(cls.get_setting(db, "rate_limit_api_window", 60))
                },
                "widget": {
                    "requests": int(cls.get_setting(db, "rate_limit_widget_requests", 100)),  # افزایش از 50 به 100
                    "window": int(cls.get_setting(db, "rate_limit_widget_window", 60))
                }
            }
        except (ValueError, TypeError) as e:
            logger.error(f"Error converting rate limit settings to int: {str(e)}")
            # If conversion fails, return default values
            return {
                "chat": {"requests": 100, "window": 60},  # افزایش از 20 به 100
                "crawl": {"requests": 10, "window": 300},  # افزایش از 5 به 10
                "api": {"requests": 200, "window": 60},   # افزایش از 100 به 200
                "widget": {"requests": 100, "window": 60}  # افزایش از 50 به 100
            }
        except Exception as e:
            logger.error(f"Error getting rate limit settings: {str(e)}")
            return {
                "chat": {"requests": 100, "window": 60},  # افزایش از 20 به 100
                "crawl": {"requests": 10, "window": 300},  # افزایش از 5 به 10
                "api": {"requests": 200, "window": 60},   # افزایش از 100 به 200
                "widget": {"requests": 100, "window": 60}  # افزایش از 50 به 100
            }
    
    @classmethod
    def set_rate_limit_settings(cls, db: Session, settings: Dict[str, Dict[str, int]]) -> bool:
        """تنظیم rate limiting"""
        try:
            for limit_type, config in settings.items():
                if "requests" in config:
                    cls.set_setting(
                        db, 
                        f"rate_limit_{limit_type}_requests", 
                        config["requests"], 
                        "integer", 
                        f"تعداد درخواست‌های مجاز برای {limit_type}",
                        "rate_limiting"
                    )
                
                if "window" in config:
                    cls.set_setting(
                        db, 
                        f"rate_limit_{limit_type}_window", 
                        config["window"], 
                        "integer", 
                        f"بازه زمانی (ثانیه) برای {limit_type}",
                        "rate_limiting"
                    )
            
            return True
        except Exception as e:
            logger.error(f"Error setting rate limit settings: {str(e)}")
            return False