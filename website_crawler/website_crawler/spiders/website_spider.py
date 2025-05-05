import scrapy
import re
from urllib.parse import urlparse

class WebsiteSpider(scrapy.Spider):
    name = "website_spider"

    def __init__(self, start_url=None, allowed_domains=None, *args, **kwargs):
        super(WebsiteSpider, self).__init__(*args, **kwargs)
        self.start_urls = [start_url] if start_url else ["https://example.com"]

        if allowed_domains:
            self.allowed_domains = [allowed_domains]
        else:
            parsed_url = urlparse(self.start_urls[0])
            self.allowed_domains = [parsed_url.netloc]

        self.visited_urls = set()

        # تنظیمات اضافی برای مدیریت HTTPS و محتوا
        self.custom_settings = {
            'DOWNLOADER_MIDDLEWARES': {
                'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
            },
            'ROBOTSTXT_OBEY': False,
            'COOKIES_ENABLED': True,
            'DOWNLOAD_TIMEOUT': 180,
            'CONCURRENT_REQUESTS': 8,
            'DOWNLOAD_DELAY': 1,
        }

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url,
                               callback=self.parse,
                               dont_filter=True,
                               headers={'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'})

    def parse(self, response):
        try:
            if response.url in self.visited_urls:
                return

            self.visited_urls.add(response.url)

            # بررسی نوع محتوا
            if not response.headers.get('Content-Type', b'').strip().lower().startswith(b'text/html'):
                self.logger.warning(f"Skipping non-HTML content at {response.url}")
                return

            title = response.css('title::text').get() or ""

            main_content_selectors = [
                'main', 'article', '.content', '#content', '.post', '.entry',
                '.page-content', '.main-content'
            ]

            content = ""
            for selector in main_content_selectors:
                if response.css(selector):
                    content_parts = response.css(f'{selector} ::text').getall()
                    content = ' '.join([part.strip() for part in content_parts if part.strip()])
                    break

            if not content:
                body_text = response.css('body ::text').getall()
                content = ' '.join([text.strip() for text in body_text if text.strip()])

            # حذف فاصله‌های اضافی و خطوط جدید
            content = re.sub(r'\s+', ' ', content).strip()

            # فیلتر کردن اسکریپت‌ها و استایل‌ها
            content = re.sub(r'<script.*?</script>', '', content, flags=re.DOTALL)
            content = re.sub(r'<style.*?</style>', '', content, flags=re.DOTALL)

            yield {
                'url': response.url,
                'title': title,
                'content': content,
                'timestamp': self.crawler.stats.get_value('start_time').isoformat(),
            }

            # پیگیری لینک‌های داخلی
            for href in response.css('a::attr(href)').getall():
                if href.startswith('#') or 'javascript:' in href:
                    continue

                url = response.urljoin(href)
                parsed_url = urlparse(url)

                if parsed_url.netloc in self.allowed_domains and url not in self.visited_urls:
                    yield scrapy.Request(
                        url,
                        callback=self.parse,
                        headers={'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'},
                        errback=self.errback_httpbin,
                        dont_filter=True
                    )

        except Exception as e:
            self.logger.error(f"Error parsing {response.url}: {str(e)}")

    def errback_httpbin(self, failure):
        self.logger.error(f"Request failed: {failure.value}")