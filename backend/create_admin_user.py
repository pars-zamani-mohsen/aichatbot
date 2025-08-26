#!/usr/bin/env python3
"""
اسکریپت ایجاد کاربر مدیر
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.database import SessionLocal
from app.database import models
from app.api.auth import get_password_hash

def create_admin_user():
    db = SessionLocal()
    try:
        # بررسی وجود کاربر admin
        admin_user = db.query(models.User).filter(models.User.email == "admin@example.com").first()
        
        if admin_user:
            print("✅ کاربر admin قبلاً وجود دارد!")
            return
        
        # ایجاد کاربر admin جدید
        admin_user = models.User(
            email="admin@example.com",
            hashed_password=get_password_hash("admin123"),
            is_active=True,
            is_verified=True,
            role="admin"
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("✅ کاربر admin با موفقیت ایجاد شد!")
        print("📧 ایمیل: admin@example.com")
        print("🔑 رمز عبور: admin123")
        print("👤 نقش: admin")
        
    except Exception as e:
        print(f"❌ خطا در ایجاد کاربر admin: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user()
