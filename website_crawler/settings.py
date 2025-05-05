
BOT_NAME = 'website_crawler'
SPIDER_MODULES = ['website_crawler.spiders']
NEWSPIDER_MODULE = 'website_crawler.spiders'
ROBOTSTXT_OBEY = True
CONCURRENT_REQUESTS = 16
DOWNLOAD_DELAY = 1
COOKIES_ENABLED = False
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'
