#!/usr/bin/env python3
"""
تست کراولر برای وب‌سایت فارسی
"""
import asyncio
import sys
import os
from pathlib import Path

# اضافه کردن مسیر backend به sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.pipeline import WebCrawlerPipeline
import logging

# تنظیم logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_persian_crawler():
    """تست کراولر برای وب‌سایت فارسی"""
    print("🔄 شروع تست کراولر فارسی...")
    
    # تست URL فارسی
    test_url = "https://fa.wikipedia.org/wiki/ایران"
    
    # تنظیمات تست
    test_settings = {
        'max_pages': 3,  # فقط 3 صفحه برای تست
        'max_depth': 2,
        'delay': 1,  # تأخیر بیشتر برای احترام به سرور
        'respect_robots': True,
        'user_agent': 'RAG-Crawler-Persian/1.0'
    }
    
    try:
        # ایجاد کراولر
        print(f"📡 ایجاد کراولر برای: {test_url}")
        crawler = WebCrawlerPipeline(test_url, test_settings)
        
        # اجرای کراول
        print("🚀 شروع کراولینگ...")
        success = await crawler.run_async()
        
        if success:
            print(f"✅ کراولینگ موفق! تعداد صفحات: {len(crawler.data)}")
            
            # نمایش نتایج
            for i, page in enumerate(crawler.data):
                print(f"\n📄 صفحه {i+1}:")
                print(f"   URL: {page['url']}")
                print(f"   عنوان: {page['title'][:100]}...")
                print(f"   متن: {page['text'][:200]}...")
                print(f"   لینک‌ها: {len(page['links'])}")
                
                # نمایش چند لینک نمونه
                if page['links']:
                    print(f"   نمونه لینک‌ها:")
                    for link in page['links'][:3]:
                        print(f"     - {link}")
            
            # بررسی فایل‌های خروجی
            output_file = crawler.output_dir / "processed_data.csv"
            if output_file.exists():
                print(f"✅ فایل خروجی ایجاد شد: {output_file}")
                
                # خواندن و نمایش محتوای فایل
                import pandas as pd
                df = pd.read_csv(output_file)
                print(f"📊 اطلاعات فایل:")
                print(f"   تعداد ردیف‌ها: {len(df)}")
                print(f"   ستون‌ها: {list(df.columns)}")
                
            else:
                print("❌ فایل خروجی ایجاد نشد!")
                
        else:
            print("❌ کراولینگ ناموفق!")
            
    except Exception as e:
        print(f"💥 خطا در تست کراولر: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 شروع تست کراولر فارسی...")
    asyncio.run(test_persian_crawler())
    print("\n🎉 تست کراولر فارسی تمام شد!")
