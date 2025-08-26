#!/usr/bin/env python3
"""
اسکریپت برای اضافه کردن فیلدهای امنیتی به دیتابیس
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.database import engine
from sqlalchemy import text

def add_security_columns():
    """اضافه کردن فیلدهای امنیتی به جدول users"""
    try:
        with engine.connect() as connection:
            # اضافه کردن فیلد تأیید ایمیل
            connection.execute(text("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE;
            """))
            
            # اضافه کردن فیلد نقش کاربری
            connection.execute(text("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS role VARCHAR DEFAULT 'user';
            """))
            
            # اضافه کردن فیلد توکن تأیید
            connection.execute(text("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS verification_token VARCHAR;
            """))
            
            # اضافه کردن فیلد توکن بازیابی رمز عبور
            connection.execute(text("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS reset_token VARCHAR;
            """))
            
            # اضافه کردن فیلد انقضای توکن بازیابی
            connection.execute(text("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS reset_token_expires TIMESTAMP;
            """))
            
            # تغییر is_active به FALSE (نیاز به فعال‌سازی)
            connection.execute(text("""
                UPDATE users SET is_active = TRUE WHERE is_active IS NULL;
            """))
            
            connection.commit()
            print("✅ فیلدهای امنیتی با موفقیت به دیتابیس اضافه شدند")
            
    except Exception as e:
        print(f"❌ خطا در اضافه کردن فیلدها: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    print("🔄 در حال اضافه کردن فیلدهای امنیتی به دیتابیس...")
    success = add_security_columns()
    if success:
        print("🎉 عملیات با موفقیت انجام شد!")
    else:
        print("💥 عملیات ناموفق بود!")
        sys.exit(1)
