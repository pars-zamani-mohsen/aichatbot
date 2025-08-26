#!/usr/bin/env python3
"""
اسکریپت تست کراولر
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

async def test_crawler():
    """تست کراولر"""
    print("🔄 شروع تست کراولر...")
    
    # تست URL
    test_url = "https://example.com"
    
    # تنظیمات تست
    test_settings = {
        'max_pages': 5,  # فقط 5 صفحه برای تست
        'max_depth': 2,
        'delay': 0.5,  # تأخیر کم برای تست
        'respect_robots': True,
        'user_agent': 'RAG-Crawler-Test/1.0'
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
            for i, page in enumerate(crawler.data[:3]):  # فقط 3 صفحه اول
                print(f"\n📄 صفحه {i+1}:")
                print(f"   URL: {page['url']}")
                print(f"   عنوان: {page['title'][:50]}...")
                print(f"   متن: {page['text'][:100]}...")
                print(f"   لینک‌ها: {len(page['links'])}")
            
            # بررسی فایل‌های خروجی
            output_file = crawler.output_dir / "processed_data.csv"
            if output_file.exists():
                print(f"✅ فایل خروجی ایجاد شد: {output_file}")
            else:
                print("❌ فایل خروجی ایجاد نشد!")
                
        else:
            print("❌ کراولینگ ناموفق!")
            
    except Exception as e:
        print(f"💥 خطا در تست کراولر: {str(e)}")
        import traceback
        traceback.print_exc()

async def test_robots_txt():
    """تست robots.txt"""
    print("\n🔄 تست robots.txt...")
    
    test_url = "https://www.google.com"
    test_settings = {
        'max_pages': 1,
        'respect_robots': True,
        'user_agent': 'RAG-Crawler-Test/1.0'
    }
    
    try:
        crawler = WebCrawlerPipeline(test_url, test_settings)
        
        # ایجاد session
        import ssl
        import aiohttp
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        crawler.session = aiohttp.ClientSession(connector=connector)
        
        # تست robots.txt
        await crawler.parse_robots_txt()
        
        print(f"✅ Robots.txt rules:")
        print(f"   Disallowed: {list(crawler.robots_rules['disallowed'])[:5]}")
        print(f"   Allowed: {list(crawler.robots_rules['allowed'])[:5]}")
        print(f"   Crawl delay: {crawler.robots_rules['crawl_delay']}")
        
        await crawler.session.close()
        
    except Exception as e:
        print(f"💥 خطا در تست robots.txt: {str(e)}")

async def test_url_validation():
    """تست اعتبارسنجی URL"""
    print("\n🔄 تست اعتبارسنجی URL...")
    
    test_urls = [
        "https://example.com/page1",
        "https://example.com/image.jpg",
        "https://example.com/script.js",
        "https://example.com/document.pdf",
        "https://otherdomain.com/page",
        "invalid-url",
        "https://example.com/page?param=value"
    ]
    
    crawler = WebCrawlerPipeline("https://example.com")
    
    for url in test_urls:
        should_crawl = crawler.should_crawl(url)
        print(f"   {url}: {'✅' if should_crawl else '❌'}")

if __name__ == "__main__":
    print("🧪 شروع تست‌های کراولر...")
    
    # اجرای تست‌ها
    asyncio.run(test_url_validation())
    asyncio.run(test_robots_txt())
    asyncio.run(test_crawler())
    
    print("\n🎉 تست‌های کراولر تمام شد!")
