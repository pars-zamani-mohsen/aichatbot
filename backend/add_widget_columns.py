#!/usr/bin/env python3
"""
اسکریپت برای اضافه کردن فیلدهای ویجت به دیتابیس
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.database import engine
from sqlalchemy import text

def add_widget_columns():
    """اضافه کردن فیلدهای ویجت به جدول websites"""
    try:
        with engine.connect() as connection:
            # اضافه کردن فیلد public_key
            connection.execute(text("""
                ALTER TABLE websites 
                ADD COLUMN IF NOT EXISTS public_key VARCHAR;
            """))
            
            # اضافه کردن فیلد widget_config
            connection.execute(text("""
                ALTER TABLE websites 
                ADD COLUMN IF NOT EXISTS widget_config JSONB;
            """))
            
            connection.commit()
            print("✅ فیلدهای ویجت با موفقیت به دیتابیس اضافه شدند")
            
    except Exception as e:
        print(f"❌ خطا در اضافه کردن فیلدها: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    print("🔄 در حال اضافه کردن فیلدهای ویجت به دیتابیس...")
    success = add_widget_columns()
    if success:
        print("🎉 عملیات با موفقیت انجام شد!")
    else:
        print("💥 عملیات ناموفق بود!")
        sys.exit(1)
