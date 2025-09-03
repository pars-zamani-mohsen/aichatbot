#!/usr/bin/env python3
"""
اسکریپت برای تنظیم collection_name در دیتابیس
"""

import os
import sys
from pathlib import Path

# اضافه کردن مسیر پروژه
sys.path.append(str(Path(__file__).parent))

from app.database.database import get_db
from app.database import models
from sqlalchemy.orm import Session
from app.database.database import engine
from app.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_collection_names():
    """تنظیم collection_name برای وب‌سایت‌هایی که آماده هستند"""
    session = Session(engine)
    
    try:
        # دریافت همه وب‌سایت‌ها
        websites = session.query(models.Website).all()
        
        for website in websites:
            logger.info(f"بررسی وب‌سایت: {website.domain} (وضعیت: {website.status})")
            
            # اگر وب‌سایت آماده است و collection_name ندارد
            if website.status == "ready" and not website.collection_name:
                # تنظیم collection_name بر اساس domain
                website.collection_name = website.domain
                if settings.DEBUG_MODE:
                    logger.info(f"تنظیم collection_name برای {website.domain}: {website.collection_name}")
            
            # اگر وب‌سایت آماده نیست اما فایل‌های کراول موجود هستند
            elif website.status != "ready":
                # بررسی وجود فایل‌های کراول
                processed_dir = Path(f"processed_data/{website.domain}")
                if processed_dir.exists() and (processed_dir / "processed_data.csv").exists():
                    website.status = "ready"
                    website.collection_name = website.domain
                    logger.info(f"تنظیم وضعیت ready برای {website.domain}")
        
        # ذخیره تغییرات
        session.commit()
        logger.info("تغییرات با موفقیت ذخیره شد")
        
        # نمایش نتیجه
        websites = session.query(models.Website).all()
        for website in websites:
            if settings.DEBUG_MODE:
                logger.info(f"ID: {website.id}, Domain: {website.domain}, Status: {website.status}, Collection: {website.collection_name}")
            
    except Exception as e:
        logger.error(f"خطا: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    fix_collection_names()
