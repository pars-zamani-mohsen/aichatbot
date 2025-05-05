# website_crawler/website_crawler/settings.py

BOT_NAME = 'website_crawler'

SPIDER_MODULES = ['website_crawler.spiders']
NEWSPIDER_MODULE = 'website_crawler.spiders'

# تنظیمات کارایی و سرعت
CONCURRENT_REQUESTS = 32
CONCURRENT_REQUESTS_PER_DOMAIN = 16
CONCURRENT_REQUESTS_PER_IP = 16
DOWNLOAD_DELAY = 0.5
DOWNLOAD_TIMEOUT = 15

# تنظیمات DNS و کش
DNSCACHE_ENABLED = True
DNS_TIMEOUT = 10

# تنظیمات اتوتراتل هوشمند
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 3
AUTOTHROTTLE_TARGET_CONCURRENCY = 16
AUTOTHROTTLE_DEBUG = False

# تنظیمات User-Agent
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# تنظیمات امنیتی و دسترسی
ROBOTSTXT_OBEY = False
COOKIES_ENABLED = False
COOKIES_DEBUG = False

# تنظیمات خروجی
FEED_EXPORT_ENCODING = 'utf-8'
#FEED_FORMAT = 'json'
#FEED_URI = 'website_crawler/output.json'
FEED_EXPORT_INDENT = 2

# محدودیت عمق کرال
DEPTH_LIMIT = 1
DEPTH_PRIORITY = 1
DEPTH_STATS_VERBOSE = True

# تنظیمات کش و حافظه
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 86400
HTTPCACHE_GZIP = True

# Retry تنظیمات
RETRY_ENABLED = True
RETRY_TIMES = 2
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429, 403]

# تنظیمات لاگ
LOG_LEVEL = 'INFO'
LOG_FILE = 'crawler.log'

# Middlewares
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': 500,
    'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
}

# پیکربندی هدرهای HTTP
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en',
    'Accept-Encoding': 'gzip, deflate, br',
}

# تنظیمات امنیتی بیشتر
DOWNLOAD_HANDLERS = {
    "http": "scrapy.core.downloader.handlers.http.HTTP10DownloadHandler",
    "https": "scrapy.core.downloader.handlers.http.HTTP10DownloadHandler",
}

# تنظیمات بافر و حافظه
REACTOR_THREADPOOL_MAXSIZE = 20
REDIRECT_ENABLED = True
REDIRECT_MAX_TIMES = 3