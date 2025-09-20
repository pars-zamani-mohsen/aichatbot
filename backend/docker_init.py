#!/usr/bin/env python3
"""
اسکریپت اولیه‌سازی برای Docker
"""

import os
import sys
import time
from pathlib import Path

# اضافه کردن مسیر app به sys.path
sys.path.append('/app')
sys.path.append('/app/app')

def wait_for_database():
    """انتظار برای آماده شدن دیتابیس"""
    print("⏳ در حال انتظار برای آماده شدن دیتابیس...")
    time.sleep(10)  # 10 ثانیه انتظار
    return True

def create_tables():
    """ایجاد جداول دیتابیس"""
    print("🏗️ در حال ایجاد جداول دیتابیس...")
    
    try:
        from app.database.database import engine
        from app.database import models
        
        models.Base.metadata.create_all(bind=engine)
        print("✅ جداول دیتابیس ایجاد شدند!")
        return True
    except Exception as e:
        print(f"❌ خطا در ایجاد جداول: {e}")
        return False

def create_admin_user():
    """ایجاد کاربر مدیر"""
    print("🔧 در حال ایجاد کاربر مدیر...")
    
    try:
        from create_admin_user import create_admin_user
        create_admin_user()
        return True
    except Exception as e:
        print(f"⚠️ خطا در ایجاد کاربر مدیر: {e}")
        return False

def main():
    """تابع اصلی"""
    print("🚀 شروع اولیه‌سازی سیستم...")
    
    # انتظار برای دیتابیس
    wait_for_database()
    
    # ایجاد جداول
    create_tables()
    
    # ایجاد کاربر مدیر
    create_admin_user()
    
    print("🎉 اولیه‌سازی سیستم با موفقیت انجام شد!")

if __name__ == "__main__":
    main()
