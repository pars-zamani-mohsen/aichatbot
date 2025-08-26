#!/usr/bin/env python3
"""
اسکریپت برای اضافه کردن فیلدهای multi-tenant به دیتابیس
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.database import engine
from sqlalchemy import text

def add_multi_tenant_columns():
    """اضافه کردن فیلدهای multi-tenant به جدول websites"""
    try:
        with engine.connect() as connection:
            # اضافه کردن فیلدهای تنظیمات کراولینگ
            connection.execute(text("""
                ALTER TABLE websites
                ADD COLUMN IF NOT EXISTS crawl_settings JSONB;
            """))
            
            # اضافه کردن فیلدهای تنظیمات RAG
            connection.execute(text("""
                ALTER TABLE websites
                ADD COLUMN IF NOT EXISTS rag_settings JSONB;
            """))
            
            # اضافه کردن فیلدهای تنظیمات ویجت
            connection.execute(text("""
                ALTER TABLE websites
                ADD COLUMN IF NOT EXISTS widget_settings JSONB;
            """))
            
            # اضافه کردن فیلد تأیید دامنه
            connection.execute(text("""
                ALTER TABLE websites
                ADD COLUMN IF NOT EXISTS domain_verified BOOLEAN DEFAULT FALSE;
            """))
            
            # اضافه کردن فیلد توکن تأیید
            connection.execute(text("""
                ALTER TABLE websites
                ADD COLUMN IF NOT EXISTS verification_token VARCHAR;
            """))
            
            connection.commit()
            print("✅ فیلدهای multi-tenant با موفقیت به دیتابیس اضافه شدند")
            
    except Exception as e:
        print(f"❌ خطا در اضافه کردن فیلدها: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    print("🔄 در حال اضافه کردن فیلدهای multi-tenant به دیتابیس...")
    success = add_multi_tenant_columns()
    if success:
        print("🎉 عملیات با موفقیت انجام شد!")
    else:
        print("💥 عملیات ناموفق بود!")
        sys.exit(1)
