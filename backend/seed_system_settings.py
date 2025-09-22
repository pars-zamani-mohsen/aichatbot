#!/usr/bin/env python3
"""
سیدر برای تنظیمات سیستم
این فایل تنظیمات پیش‌فرض سیستم را در دیتابیس ایجاد می‌کند
"""

import os
import sys
from pathlib import Path

# اضافه کردن مسیر backend به sys.path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.database.database import get_db
from app.database.models import SystemSettings
from sqlalchemy.orm import Session
from sqlalchemy import text

def seed_system_settings():
    """ایجاد تنظیمات پیش‌فرض سیستم"""
    
    # تنظیمات پیش‌فرض
    default_settings = [
        # تنظیمات عمومی
        {
            "key": "siteName",
            "value": "چت بات هوشمند پارس",
            "value_type": "string",
            "description": "نام سایت",
            "category": "general",
            "is_public": True
        },
        {
            "key": "siteDescription",
            "value": "سیستم چت‌بات هوشمند با قابلیت RAG",
            "value_type": "string",
            "description": "توضیحات سایت",
            "category": "general",
            "is_public": True
        },
        {
            "key": "systemTimezone",
            "value": "Asia/Tehran",
            "value_type": "string",
            "description": "منطقه زمانی سیستم",
            "category": "general",
            "is_public": False
        },
        
        # تنظیمات ایمیل
        {
            "key": "smtpServer",
            "value": "smtp.gmail.com",
            "value_type": "string",
            "description": "سرور SMTP",
            "category": "email",
            "is_public": False
        },
        {
            "key": "smtpPort",
            "value": "587",
            "value_type": "integer",
            "description": "پورت SMTP",
            "category": "email",
            "is_public": False
        },
        {
            "key": "smtpUsername",
            "value": "noreply@example.com",
            "value_type": "string",
            "description": "نام کاربری SMTP",
            "category": "email",
            "is_public": False
        },
        {
            "key": "emailFrom",
            "value": "noreply@example.com",
            "value_type": "string",
            "description": "آدرس ایمیل فرستنده",
            "category": "email",
            "is_public": False
        },
        
        # تنظیمات امنیت
        {
            "key": "sessionTimeout",
            "value": "30",
            "value_type": "integer",
            "description": "مدت زمان انقضای جلسه (دقیقه)",
            "category": "security",
            "is_public": False
        },
        {
            "key": "maxLoginAttempts",
            "value": "5",
            "value_type": "integer",
            "description": "حداکثر تعداد تلاش برای ورود",
            "category": "security",
            "is_public": False
        },
        {
            "key": "passwordMinLength",
            "value": "6",
            "value_type": "integer",
            "description": "حداقل طول رمز عبور",
            "category": "security",
            "is_public": False
        },
        {
            "key": "requireEmailVerification",
            "value": "True",
            "value_type": "boolean",
            "description": "نیاز به تأیید ایمیل",
            "category": "security",
            "is_public": False
        },
        
        # تنظیمات RAG
        {
            "key": "defaultK",
            "value": "5",
            "value_type": "integer",
            "description": "تعداد اسناد پیش‌فرض برای بازیابی",
            "category": "rag",
            "is_public": False
        },
        {
            "key": "maxResponseLength",
            "value": "500",
            "value_type": "integer",
            "description": "حداکثر طول پاسخ",
            "category": "rag",
            "is_public": False
        },
        {
            "key": "defaultTemperature",
            "value": "0.7",
            "value_type": "float",
            "description": "دمای پیش‌فرض برای تولید متن",
            "category": "rag",
            "is_public": False
        },
        {
            "key": "defaultLanguage",
            "value": "fa",
            "value_type": "string",
            "description": "زبان پیش‌فرض",
            "category": "rag",
            "is_public": False
        },
        {
            "key": "enableOpenAI",
            "value": "True",
            "value_type": "boolean",
            "description": "فعال‌سازی OpenAI",
            "category": "rag",
            "is_public": False
        },
        
        # تنظیمات کراولر
        {
            "key": "respectRobotsTxt",
            "value": "True",
            "value_type": "boolean",
            "description": "احترام به robots.txt",
            "category": "crawler",
            "is_public": False
        },
        {
            "key": "userAgent",
            "value": "RAG-Chatbot-Crawler/1.0",
            "value_type": "string",
            "description": "User Agent برای کراولر",
            "category": "crawler",
            "is_public": False
        },
        {
            "key": "crawlDelay",
            "value": "1",
            "value_type": "integer",
            "description": "تأخیر بین درخواست‌های کراول (ثانیه)",
            "category": "crawler",
            "is_public": False
        },
        {
            "key": "maxPagesPerSite",
            "value": "200",
            "value_type": "integer",
            "description": "حداکثر تعداد صفحات برای هر سایت",
            "category": "crawler",
            "is_public": False
        },
        
        # تنظیمات اعلان‌ها
        {
            "key": "emailNotifications",
            "value": "True",
            "value_type": "boolean",
            "description": "فعال‌سازی اعلان‌های ایمیل",
            "category": "notifications",
            "is_public": False
        },
        {
            "key": "notifyOnError",
            "value": "True",
            "value_type": "boolean",
            "description": "اعلان در صورت خطا",
            "category": "notifications",
            "is_public": False
        },
        {
            "key": "notifyOnNewUser",
            "value": "True",
            "value_type": "boolean",
            "description": "اعلان در صورت کاربر جدید",
            "category": "notifications",
            "is_public": False
        },
        {
            "key": "slackNotifications",
            "value": "False",
            "value_type": "boolean",
            "description": "فعال‌سازی اعلان‌های Slack",
            "category": "notifications",
            "is_public": False
        },
        
        # تنظیمات Rate Limiting
        {
            "key": "rate_limit_chat_requests",
            "value": "100",
            "value_type": "integer",
            "description": "تعداد درخواست‌های مجاز برای chat",
            "category": "rate_limiting",
            "is_public": False
        },
        {
            "key": "rate_limit_chat_window",
            "value": "60",
            "value_type": "integer",
            "description": "بازه زمانی (ثانیه) برای chat",
            "category": "rate_limiting",
            "is_public": False
        },
        {
            "key": "rate_limit_crawl_requests",
            "value": "50",
            "value_type": "integer",
            "description": "تعداد درخواست‌های مجاز برای crawl",
            "category": "rate_limiting",
            "is_public": False
        },
        {
            "key": "rate_limit_crawl_window",
            "value": "300",
            "value_type": "integer",
            "description": "بازه زمانی (ثانیه) برای crawl",
            "category": "rate_limiting",
            "is_public": False
        },
        {
            "key": "rate_limit_api_requests",
            "value": "200",
            "value_type": "integer",
            "description": "تعداد درخواست‌های مجاز برای api",
            "category": "rate_limiting",
            "is_public": False
        },
        {
            "key": "rate_limit_api_window",
            "value": "60",
            "value_type": "integer",
            "description": "بازه زمانی (ثانیه) برای api",
            "category": "rate_limiting",
            "is_public": False
        },
        {
            "key": "rate_limit_widget_requests",
            "value": "100",
            "value_type": "integer",
            "description": "تعداد درخواست‌های مجاز برای widget",
            "category": "rate_limiting",
            "is_public": False
        },
        {
            "key": "rate_limit_widget_window",
            "value": "60",
            "value_type": "integer",
            "description": "بازه زمانی (ثانیه) برای widget",
            "category": "rate_limiting",
            "is_public": False
        }
    ]
    
    try:
        # اتصال به دیتابیس
        db = next(get_db())
        
        print("🌱 شروع seeding تنظیمات سیستم...")
        
        # بررسی وجود تنظیمات
        existing_settings = db.query(SystemSettings).count()
        print(f"📊 تعداد تنظیمات موجود: {existing_settings}")
        
        # ایجاد تنظیمات جدید
        created_count = 0
        updated_count = 0
        
        for setting_data in default_settings:
            # بررسی وجود تنظیم
            existing_setting = db.query(SystemSettings).filter(
                SystemSettings.key == setting_data["key"]
            ).first()
            
            if existing_setting:
                # به‌روزرسانی تنظیم موجود
                existing_setting.value = setting_data["value"]
                existing_setting.value_type = setting_data["value_type"]
                existing_setting.description = setting_data["description"]
                existing_setting.category = setting_data["category"]
                existing_setting.is_public = setting_data["is_public"]
                updated_count += 1
                print(f"🔄 به‌روزرسانی: {setting_data['key']}")
            else:
                # ایجاد تنظیم جدید
                new_setting = SystemSettings(**setting_data)
                db.add(new_setting)
                created_count += 1
                print(f"➕ ایجاد: {setting_data['key']}")
        
        # ذخیره تغییرات
        db.commit()
        
        print(f"\n✅ Seeding تکمیل شد!")
        print(f"📈 آمار:")
        print(f"   - ایجاد شده: {created_count}")
        print(f"   - به‌روزرسانی شده: {updated_count}")
        print(f"   - کل تنظیمات: {db.query(SystemSettings).count()}")
        
    except Exception as e:
        print(f"❌ خطا در seeding: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_system_settings()
