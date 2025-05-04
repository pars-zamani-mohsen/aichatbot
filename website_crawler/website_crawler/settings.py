# website_crawler/website_crawler/settings.py  

BOT_NAME = 'website_crawler'  

SPIDER_MODULES = ['website_crawler.spiders']  
NEWSPIDER_MODULE = 'website_crawler.spiders'  

# تنظیم User-Agent  
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'  

# احترام به robots.txt  
ROBOTSTXT_OBEY = True  

# محدودیت سرعت درخواست‌ها (بر حسب ثانیه)  
DOWNLOAD_DELAY = 1  

# تنظیمات همزمانی  
CONCURRENT_REQUESTS = 8

FEED_EXPORT_ENCODING = 'utf-8'

# تنظیمات کوکی‌ها و سشن  
COOKIES_ENABLED = True  

# خروجی را در فایل JSON ذخیره کنید  
FEED_FORMAT = 'json'  
FEED_URI = 'output.json'  

# تنظیم حداکثر عمق پیمایش (اختیاری)  
DEPTH_LIMIT = 1

# خط‌های میانی (Middlewares)  
DOWNLOADER_MIDDLEWARES = {  
   'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,  
   'scrapy.downloadermiddlewares.retry.RetryMiddleware': 500,  
}  

# تنظیمات بازپخش (Retry)  
RETRY_ENABLED = True  
RETRY_TIMES = 3  # تعداد دفعات تلاش مجدد  
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]  # کدهای HTTP برای تلاش مجدد  
