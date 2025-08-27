#!/usr/bin/env python3
"""
اسکریپت برای اضافه کردن فیلد last_login به جدول users
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.database.database import engine

def add_last_login_column():
    """اضافه کردن فیلد last_login به جدول users"""
    try:
        with engine.connect() as connection:
            # بررسی وجود فیلد
            result = connection.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'last_login'
            """))
            
            if result.fetchone():
                print("فیلد last_login قبلاً وجود دارد.")
                return
            
            # اضافه کردن فیلد
            connection.execute(text("""
                ALTER TABLE users 
                ADD COLUMN last_login TIMESTAMP WITH TIME ZONE
            """))
            
            connection.commit()
            print("فیلد last_login با موفقیت اضافه شد.")
            
    except Exception as e:
        print(f"خطا در اضافه کردن فیلد: {e}")
        raise

if __name__ == "__main__":
    add_last_login_column()
