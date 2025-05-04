# website_spider.py  

import scrapy  
import re  
from urllib.parse import urlparse  

class WebsiteSpider(scrapy.Spider):  
    name = "website_spider"  
    
    def __init__(self, start_url=None, allowed_domains=None, *args, **kwargs):  
        super(WebsiteSpider, self).__init__(*args, **kwargs)  
        # URL شروع را تنظیم کنید  
        self.start_urls = [start_url] if start_url else ["https://example.com"]  
        
        # دامنه‌های مجاز برای خزش را تنظیم کنید  
        if allowed_domains:  
            self.allowed_domains = [allowed_domains]  
        else:  
            # استخراج دامنه از URL شروع  
            parsed_url = urlparse(self.start_urls[0])  
            self.allowed_domains = [parsed_url.netloc]  
        
        self.visited_urls = set()  
    
    def parse(self, response):  
        # اگر URL را قبلاً بازدید کرده‌ایم، پردازش را متوقف کنید  
        if response.url in self.visited_urls:  
            return  
        
        self.visited_urls.add(response.url)  
        
        # استخراج متن از صفحه  
        title = response.css('title::text').get() or ""  
        
        # استخراج محتوای اصلی صفحه  
        # ما به طور خاص محتوای مفید را هدف قرار می‌دهیم و نه منوها و فوترها  
        main_content_selectors = [  
            'main', 'article', '.content', '#content', '.post', '.entry',  
            '.page-content', '.main-content'  
        ]  
        
        content = ""  
        for selector in main_content_selectors:  
            if response.css(selector):  
                # استخراج متن از همه المان‌های داخل محتوای اصلی  
                content_parts = response.css(f'{selector} ::text').getall()  
                content = ' '.join(content_parts).strip()  
                break  
        
        # اگر هیچ‌کدام از سلکتورهای بالا پیدا نشد، از کل بدنه صفحه استفاده کنید  
        if not content:  
            body_text = response.css('body ::text').getall()  
            content = ' '.join(body_text).strip()  
        
        # حذف فاصله‌های اضافی و خطوط جدید  
        content = re.sub(r'\s+', ' ', content).strip()  
        
        # ذخیره داده‌های استخراج شده  
        yield {  
            'url': response.url,  
            'title': title,  
            'content': content,  
            'timestamp': self.crawler.stats.get_value('start_time').isoformat(),  
        }  
        
        # پیگیری لینک‌های داخلی  
        for href in response.css('a::attr(href)').getall():  
            # نادیده گرفتن لینک‌های خارجی یا خاص  
            # فقط لینک‌های داخلی سایت را دنبال کنید  
            if href.startswith('#') or 'javascript:' in href:  
                continue  
                
            # ساخت URL کامل  
            url = response.urljoin(href)  
            
            # اطمینان از اینکه URL داخل دامنه مجاز است  
            parsed_url = urlparse(url)  
            if parsed_url.netloc in self.allowed_domains:  
                yield scrapy.Request(url, callback=self.parse)  
