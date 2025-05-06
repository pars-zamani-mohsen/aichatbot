from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
import sys
import os
import json
import pandas as pd
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin, urlparse
import time
from datetime import datetime
import re
import logging
from pathlib import Path
import argparse

class WebCrawlerPipeline:
    def __init__(self, start_url, max_pages=10):
        self.start_url = start_url.rstrip('/')
        self.max_pages = max_pages
        self.domain = urlparse(start_url).netloc
        self.visited_urls = set()
        self.data = []

        # تنظیم مسیرها
        self.base_dir = Path('processed_data')
        self.site_dir = self.base_dir / self.domain
        self.site_dir.mkdir(parents=True, exist_ok=True)

        # تنظیم لاگ در پوشه سایت
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.site_dir / 'crawler.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

        # اطلاعات خزش
        self.crawl_info = {
            'start_url': start_url,
            'domain': self.domain,
            'max_pages': max_pages,
            'start_time': datetime.now().isoformat()
        }

        # الگوهای صفحات مهم
        self.priority_patterns = [
            # صفحات درباره ما
            '/about', '/about-us', '/about_us', '/درباره-ما', '/درباره',
            # صفحات تماس
            '/contact', '/contact-us', '/contact_us', '/تماس-با-ما', '/تماس',
            # صفحات خدمات
            '/services', '/our-services', '/خدمات', '/خدمات-ما',
            # سؤالات متداول
            '/faq', '/faqs', '/سوالات-متداول',
            # قیمت‌گذاری
            '/pricing', '/prices', '/قیمت', '/تعرفه',
            # صفحه تیم
            '/team', '/our-team', '/تیم-ما', '/تیم'
        ]

    def get_priority_score(self, url):
        """تعیین اولویت URL"""
        url_lower = url.lower()
        for i, pattern in enumerate(self.priority_patterns):
            if pattern in url_lower:
                return i
        return len(self.priority_patterns)

    def process_url(self, url_info):
        """پردازش یک URL"""
        url, depth = url_info
        if url in self.visited_urls:
            return None

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0...',
                'Connection': 'keep-alive'
            }
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                # ... کد پردازش محتوا ...
                return {'url': url, 'title': title, 'content': content}
        except Exception as e:
            self.logger.error(f"خطا در {url}: {str(e)}")
        return None

    def crawl(self):
        """خزش موازی وبسایت با اولویت‌بندی صفحات"""
        to_visit = [(self.start_url, 0)]  # (url, depth)
        max_workers = 10  # تعداد threads همزمان

        print(f"\n=== شروع خزش موازی از {self.start_url} ===")
        print(f"تعداد threads همزمان: {max_workers}")

        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Connection': 'keep-alive'
        })

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            while to_visit and len(self.visited_urls) < self.max_pages:
                # مرتب‌سازی URLs براساس اولویت
                to_visit.sort(key=lambda x: (self.get_priority_score(x[0]), x[1]))

                # انتخاب URLs برای پردازش موازی
                current_batch = []
                while to_visit and len(current_batch) < max_workers:
                    url, depth = to_visit.pop(0)
                    clean_url = self._clean_url(url)  # نرمال‌سازی URL
                    if clean_url not in self.visited_urls:
                        current_batch.append((clean_url, depth))
                        self.visited_urls.add(clean_url)

                if not current_batch:
                    continue

                # اجرای موازی درخواست‌ها
                future_to_url = {
                    executor.submit(self._process_page, session, url, depth): (url, depth)
                    for url, depth in current_batch
                }

                # جمع‌آوری نتایج
                for future in concurrent.futures.as_completed(future_to_url):
                    url, depth = future_to_url[future]
                    try:
                        result = future.result()
                        if result:
                            self.data.append(result['data'])
                            # اضافه کردن URLهای جدید با نرمال‌سازی
                            for new_url in result.get('new_urls', []):
                                clean_new_url = self._clean_url(new_url)
                                if clean_new_url not in self.visited_urls:
                                    to_visit.append((clean_new_url, depth + 1))
                    except Exception as e:
                        self.logger.error(f"خطا در پردازش {url}: {str(e)}")

                time.sleep(0.1)

        print(f"\n=== خزش به پایان رسید ===")
        print(f"تعداد صفحات پردازش شده: {len(self.data)}")
        print(f"تعداد URLs بازدید شده: {len(self.visited_urls)}")

    def _clean_url(self, url):
        """نرمال‌سازی URL"""
        parsed = urlparse(url)
        # حذف fragment و query
        cleaned = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        # حذف / اضافی از انتها
        return cleaned.rstrip('/')

    def _process_page(self, session, url, depth):
        """پردازش یک صفحه وب"""
        # بررسی پسوند URL قبل از پردازش
        ignored_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.pdf', '.mp4', '.webp',
                             '.css', '.js', '.ico', '.xml', '.mp3', '.wav', '.webm')
        if url.lower().endswith(ignored_extensions):
            return None

        clean_url = self._clean_url(url)
        try:
            response = session.get(clean_url, timeout=10)
            response.raise_for_status()

            # بررسی Content-Type
            content_type = response.headers.get('content-type', '').lower()
            if not content_type.startswith('text/html'):
                return None

            soup = BeautifulSoup(response.text, 'html.parser')

            # استخراج عنوان
            title = soup.title.string if soup.title else ''

            # حذف تگ‌های نامربوط
            for tag in soup(['script', 'style', 'iframe', 'noscript']):
                tag.decompose()

            # استخراج محتوا
            content = ""

            # اول از محتوای اصلی
            main_content = soup.find(['main', 'article', '#content', '.content', '[role="main"]'])
            if main_content:
                content = main_content.get_text(separator=' ', strip=True)
            else:
                # اگر محتوای اصلی پیدا نشد، از کل body استفاده کن
                body = soup.find('body')
                if body:
                    content = body.get_text(separator=' ', strip=True)

            # تمیزسازی محتوا
            content = self._clean_text(content)

            if len(content) > 100:  # حداقل 100 کاراکتر
                # استخراج لینک‌های جدید
                new_urls = []
                if depth < 3:  # افزایش عمق خزش به 3
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        if href.startswith('/') or href.startswith(self.start_url):
                            full_url = urljoin(clean_url, href)
                            if self.domain in full_url and not full_url.endswith(('.jpg', '.jpeg', '.png', '.gif', '.pdf')):
                                new_urls.append(full_url)

                chunk_id = f"{len(self.data)}_{int(time.time())}_{uuid4().hex[:8]}"
                print(f"✓ پردازش {url} - {len(content)} کاراکتر")

                return {
                    'data': {
                        'url': url,
                        'title': self._clean_text(title),
                        'content': content,
                        'chunk_id': chunk_id,
                        'timestamp': datetime.now().isoformat()
                    },
                    'new_urls': list(set(new_urls))  # حذف URLهای تکراری
                }
            else:
                print(f"× رد {url} - محتوای ناکافی ({len(content)} کاراکتر)")
                return None

        except Exception as e:
            self.logger.error(f"خطا در دریافت {url}: {str(e)}")
            return None

    def _clean_text(self, text):
        """تمیزسازی متن"""
        if not isinstance(text, str):
            return ""

        # حذف کاراکترهای خاص
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)

        # حذف فاصله‌های اضافی
        text = re.sub(r'\s+', ' ', text)

        # حذف خطوط خالی
        text = re.sub(r'\n\s*\n', '\n', text)

        # تمیز کردن نهایی
        return text.strip()

    def save_results(self):
        """ذخیره نتایج"""
        if not self.data:
            print("\nهیچ داده‌ای جمع‌آوری نشد!")
            return False

        try:
            # بروزرسانی اطلاعات خزش
            self.crawl_info.update({
                'end_time': datetime.now().isoformat(),
                'pages_crawled': len(self.data),
                'visited_urls': list(self.visited_urls)
            })

            # ذخیره اطلاعات خزش
            with open(self.site_dir / 'crawl_info.json', 'w', encoding='utf-8') as f:
                json.dump(self.crawl_info, f, ensure_ascii=False, indent=2)

            # تبدیل داده‌ها به DataFrame
            df = pd.DataFrame(self.data)

            # اطمینان از وجود ستون‌های ضروری
            required_columns = ['url', 'title', 'content', 'chunk_id']
            for col in required_columns:
                if col not in df.columns:
                    df[col] = ''

            # حذف ردیف‌های خالی یا نامعتبر
            df = df.dropna(subset=['content'])
            df = df[df['content'].str.len() > 100]  # حداقل 100 کاراکتر محتوا

            if len(df) == 0:
                raise ValueError("هیچ داده معتبری برای ذخیره وجود ندارد!")

            # ذخیره CSV با encoding مناسب
            df.to_csv(self.site_dir / 'processed_data.csv', index=False, encoding='utf-8-sig')

            # ذخیره JSON
            with open(self.site_dir / 'cleaned_data.json', 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)

            print(f"\n=== نتایج برای {self.domain} ذخیره شدند ===")
            print(f"تعداد صفحات پردازش شده: {len(df)}")
            print(f"مسیر خروجی: {self.site_dir}")

            return True

        except Exception as e:
            self.logger.error(f"خطا در ذخیره نتایج: {str(e)}")
            return False

    def run(self):
        """اجرای کامل پایپلاین"""
        start_time = time.time()

        try:
            self.crawl()
            self.save_results()

            duration = time.time() - start_time
            print(f"\nزمان اجرا: {duration:.2f} ثانیه")

            return True

        except Exception as e:
            self.logger.error(f"خطا در اجرای پایپلاین: {str(e)}")
            return False

def parse_args():
    parser = argparse.ArgumentParser(description='خزش وبسایت با اولویت صفحات مهم')
    parser.add_argument('url', help='آدرس شروع خزش')
    parser.add_argument('--max-pages', type=int, default=10,
                      help='حداکثر تعداد صفحات برای خزش')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    crawler = WebCrawlerPipeline(args.url, args.max_pages)
    success = crawler.run()
    sys.exit(0 if success else 1)