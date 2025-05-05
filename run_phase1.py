import os
import json
import pandas as pd
import re
import nltk
from pathlib import Path
import subprocess
import shutil
import logging
import ssl
import requests
import sys
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin, urlparse
import time

class WebCrawlerPipeline:
    def __init__(self, start_url, max_pages=10):
        self.start_url = start_url
        self.max_pages = max_pages
        self.domain = urlparse(start_url).netloc
        self.visited_urls = set()
        self.output_dir = Path('processed_data')
        self.output_dir.mkdir(exist_ok=True)

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.output_dir / 'crawler.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def setup_scrapy(self):
        """Set up Scrapy environment and create necessary files"""
        spider_dir = Path('website_crawler/spiders')
        spider_dir.mkdir(parents=True, exist_ok=True)

        settings_code = '''
BOT_NAME = 'website_crawler'
SPIDER_MODULES = ['website_crawler.spiders']
NEWSPIDER_MODULE = 'website_crawler.spiders'
ROBOTSTXT_OBEY = True
CONCURRENT_REQUESTS = 16
DOWNLOAD_DELAY = 1
COOKIES_ENABLED = False
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'
'''

        spider_code = '''
import scrapy
from urllib.parse import urlparse

class WebsiteSpider(scrapy.Spider):
    name = 'website_spider'

    def __init__(self, start_url=None, *args, **kwargs):
        super(WebsiteSpider, self).__init__(*args, **kwargs)
        self.start_urls = [start_url] if start_url else []
        self.allowed_domains = [urlparse(start_url).netloc] if start_url else []

    def parse(self, response):
        # Extract and yield current page data
        yield {
            'url': response.url,
            'title': ' '.join(response.css('title::text').getall()),
            'content': ' '.join(response.css('p::text, article::text').getall()),
            'timestamp': datetime.now().isoformat()
        }

        # Follow links within the same domain
        for href in response.css('a::attr(href)').getall():
            url = response.urljoin(href)
            if urlparse(url).netloc == self.allowed_domains[0]:
                yield scrapy.Request(url, callback=self.parse)
'''

        # Create necessary files
        Path('website_crawler/settings.py').write_text(settings_code)
        Path('website_crawler/__init__.py').touch()
        Path('website_crawler/spiders/__init__.py').touch()
        Path('website_crawler/spiders/website_spider.py').write_text(spider_code)

    def crawl_with_requests(self):
        """Crawl website using requests and BeautifulSoup"""
        collected_data = []
        queue = [(self.start_url, 0)]

        while queue and len(self.visited_urls) < self.max_pages:
            current_url, depth = queue.pop(0)

            if current_url in self.visited_urls or depth > 2:
                continue

            try:
                self.logger.info(f"دریافت {current_url}")
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                }

                response = requests.get(
                    current_url,
                    headers=headers,
                    verify=False,
                    timeout=30
                )
                response.raise_for_status()

                soup = BeautifulSoup(response.content, 'html.parser')

                # Extract data
                data = {
                    'url': current_url,
                    'title': soup.title.string if soup.title else '',
                    'content': ' '.join(p.get_text() for p in soup.find_all(['p', 'article'])),
                    'timestamp': datetime.now().isoformat()
                }

                collected_data.append(data)
                self.visited_urls.add(current_url)

                # Find next links
                if depth < 2:
                    for link in soup.find_all('a', href=True):
                        next_url = urljoin(current_url, link['href'])
                        if (urlparse(next_url).netloc == self.domain and
                            next_url not in self.visited_urls):
                            queue.append((next_url, depth + 1))

                time.sleep(1)  # Be polite

            except Exception as e:
                self.logger.error(f"خطا در دریافت {current_url}: {e}")
                continue

        return collected_data

    def run_crawler(self):
        """Run crawler with fallback mechanism"""
        print("\n=== اجرای خزنده ===")

        try:
            # Try Scrapy first
            self.setup_scrapy()
            env = os.environ.copy()
            env['PYTHONPATH'] = str(Path.cwd())

            result = subprocess.run([
                sys.executable, '-m', 'scrapy', 'crawl',
                'website_spider',
                '-a', f'start_url={self.start_url}',
                '-o', 'output.json'
            ], env=env, capture_output=True, text=True, timeout=300)

            if result.returncode != 0:
                raise subprocess.CalledProcessError(result.returncode, result.args)

        except Exception as e:
            self.logger.error(f"خطا در اجرای Scrapy: {e}")
            self.logger.info("استفاده از روش جایگزین...")

            # Fallback to requests
            data = self.crawl_with_requests()

            # Save collected data
            with open('output.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    def process_data(self):
        """Process and clean collected data"""
        print("\n=== پردازش و تمیزسازی داده‌ها ===")

        try:
            if not Path('output.json').exists():
                raise FileNotFoundError("فایل output.json یافت نشد")

            with open('output.json', 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    raise ValueError("فایل JSON خالی است")

                data = json.loads(content)

            if not isinstance(data, list):
                data = [data]

            # Process and clean data
            processed_data = []
            for item in data:
                if isinstance(item, dict):
                    processed_item = {
                        'url': str(item.get('url', '')),
                        'title': self._clean_text(str(item.get('title', ''))),
                        'content': self._clean_text(str(item.get('content', ''))),
                        'timestamp': str(item.get('timestamp', datetime.now().isoformat()))
                    }
                    if processed_item['content']:
                        processed_data.append(processed_item)

            if processed_data:
                # Save to CSV
                df = pd.DataFrame(processed_data)
                output_file = self.output_dir / 'processed_data.csv'
                df.to_csv(output_file, index=False, encoding='utf-8')

                # Save cleaned JSON
                cleaned_json = self.output_dir / 'cleaned_data.json'
                with open(cleaned_json, 'w', encoding='utf-8') as f:
                    json.dump(processed_data, f, ensure_ascii=False, indent=2)

                print(f"داده‌ها با موفقیت پردازش و در {self.output_dir} ذخیره شدند")
                print(f"تعداد صفحات پردازش شده: {len(processed_data)}")
            else:
                raise ValueError("هیچ داده معتبری یافت نشد")

        except Exception as e:
            self.logger.error(f"خطا در پردازش داده‌ها: {e}")
            self._create_empty_files()

    def _clean_text(self, text):
        """Clean and normalize text with improved handling of Persian text"""
        if not isinstance(text, str):
            return ""

        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)

        # Keep Persian/Arabic characters, numbers, and basic punctuation
        text = re.sub(r'[^\w\s\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF.,?!:;-]', '', text)

        # Normalize Persian/Arabic numbers
        number_map = {
            '١': '1', '٢': '2', '٣': '3', '٤': '4', '٥': '5',
            '٦': '6', '٧': '7', '٨': '8', '٩': '9', '٠': '0'
        }
        for ar, en in number_map.items():
            text = text.replace(ar, en)

        return text.strip()

    def _create_empty_files(self):
        """Create empty files with proper headers"""
        # Create empty CSV
        pd.DataFrame(columns=['url', 'title', 'content', 'timestamp']
                   ).to_csv(self.output_dir / 'processed_data.csv', index=False)

        # Create empty JSON
        with open(self.output_dir / 'cleaned_data.json', 'w', encoding='utf-8') as f:
            json.dump([], f)

    def run(self):
        """Run the complete pipeline"""
        start_time = time.time()
        print(f"شروع فرآیند خزش و پردازش برای {self.start_url}")

        # Disable SSL verification
        ssl._create_default_https_context = ssl._create_unverified_context
        requests.packages.urllib3.disable_warnings()

        # Run pipeline
        self.run_crawler()
        self.process_data()

        # Report execution time
        execution_time = time.time() - start_time
        print(f"\n=== فرآیند با موفقیت به پایان رسید ===")
        print(f"زمان اجرا: {execution_time:.2f} ثانیه")
        print(f"تعداد صفحات بازدید شده: {len(self.visited_urls)}")
        print(f"داده‌های پردازش شده در پوشه {self.output_dir} ذخیره شدند.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
        max_pages = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        crawler = WebCrawlerPipeline(url, max_pages)
        crawler.run()
    else:
        print("لطفاً URL سایت مورد نظر را وارد کنید:")
        print("مثال: python run_phase1.py https://example.com [max_pages]")