#!/usr/bin/env python3
"""
اسکریپت ایجاد کاربر مدیر اولیه
این اسکریپت یک کاربر مدیر با ایمیل و رمز عبور پیش‌فرض ایجاد می‌کند
"""

import os
import sys
from pathlib import Path

# اضافه کردن مسیر app به sys.path
sys.path.append(str(Path(__file__).parent / "app"))

from app.database.database import SessionLocal
from app.database import models
from app.api.auth import get_password_hash
from app.config import settings

def create_admin_user():
    """ایجاد کاربر مدیر اولیه"""
    
    # تنظیمات پیش‌فرض
    admin_email = os.getenv("ADMIN_EMAIL", "admin@gmail.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123456#")
    
    print(f"🔧 در حال ایجاد کاربر مدیر...")
    print(f"📧 ایمیل: {admin_email}")
    
    # اتصال به دیتابیس
    db = SessionLocal()
    
    try:
        # بررسی وجود کاربر با این ایمیل
        existing_user = db.query(models.User).filter(models.User.email == admin_email).first()
        
        if existing_user:
            if existing_user.role == "admin":
                print(f"✅ کاربر مدیر با ایمیل {admin_email} قبلاً وجود دارد")
                return
            else:
                # تبدیل کاربر موجود به مدیر
                existing_user.role = "admin"
                existing_user.is_active = True
                existing_user.is_verified = True
                existing_user.hashed_password = get_password_hash(admin_password)
                db.commit()
                print(f"✅ کاربر {admin_email} به مدیر تبدیل شد")
                return
        
        # ایجاد کاربر مدیر جدید
        hashed_password = get_password_hash(admin_password)
        
        admin_user = models.User(
            email=admin_email,
            hashed_password=hashed_password,
            is_active=True,
            is_verified=True,
            role="admin"
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print(f"✅ کاربر مدیر با موفقیت ایجاد شد!")
        print(f"📧 ایمیل: {admin_email}")
        print(f"🔑 رمز عبور: {admin_password}")
        print(f"🆔 شناسه کاربر: {admin_user.id}")
        
    except Exception as e:
        print(f"❌ خطا در ایجاد کاربر مدیر: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def main():
    """تابع اصلی"""
    print("🚀 شروع ایجاد کاربر مدیر اولیه...")
    
    try:
        create_admin_user()
        print("🎉 عملیات با موفقیت انجام شد!")
        
    except Exception as e:
        print(f"💥 خطا: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
