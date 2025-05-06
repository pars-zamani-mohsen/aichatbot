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

    def crawl(self):
        """خزش وبسایت با اولویت‌بندی صفحات"""
        to_visit = [(self.start_url, 0)]  # (url, depth)

        print(f"\n=== شروع خزش از {self.start_url} ===")
        print("صفحات مهم در اولویت خزش قرار دارند.")

        while to_visit and len(self.visited_urls) < self.max_pages:
            to_visit.sort(key=lambda x: (self.get_priority_score(x[0]), x[1]))
            current_url, depth = to_visit.pop(0)

            if current_url in self.visited_urls:
                continue

            try:
                print(f"\nدریافت: {current_url}")
                print(f"اولویت: {self.get_priority_score(current_url)}")

                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }

                response = requests.get(current_url, headers=headers, timeout=10)
                self.visited_urls.add(current_url)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')

                    # استخراج عنوان
                    title = soup.title.string if soup.title else ''

                    # استخراج محتوا با الگوی جامع‌تر
                    content_elements = soup.find_all(['p', 'article', 'section', 'div', 'main', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                    content = ' '.join([elem.get_text(strip=True) for elem in content_elements if elem.get_text(strip=True)])

                    # فقط اگر محتوای معنی‌دار داشته باشیم ذخیره می‌کنیم
                    if len(content.strip()) > 100:  # حداقل 100 کاراکتر
                        self.data.append({
                            'url': current_url,
                            'title': self._clean_text(title),
                            'content': self._clean_text(content),
                            'chunk_id': len(self.data),
                            'timestamp': datetime.now().isoformat()
                        })
                        print(f"محتوا با {len(content)} کاراکتر استخراج شد.")
                    else:
                        print("محتوای کافی یافت نشد.")

                    # جمع‌آوری لینک‌های جدید
                    if depth < 2:
                        links = soup.find_all('a', href=True)
                        new_urls = []
                        for link in links:
                            url = urljoin(current_url, link['href'])
                            parsed_url = urlparse(url)
                            # فقط لینک‌های معتبر داخلی را اضافه می‌کنیم
                            if (parsed_url.netloc == self.domain and
                                parsed_url.scheme in ['http', 'https'] and
                                not any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.pdf']) and
                                url not in self.visited_urls):
                                new_urls.append((url, depth + 1))

                        # مرتب‌سازی لینک‌های جدید براساس اولویت
                        new_urls.sort(key=lambda x: self.get_priority_score(x[0]))
                        to_visit.extend(new_urls)

                    time.sleep(1)  # رعایت ادب در خزش

                else:
                    self.logger.warning(f"خطای {response.status_code} برای {current_url}")

            except Exception as e:
                self.logger.error(f"خطا در دریافت {current_url}: {str(e)}")

        print(f"\nتعداد صفحات پردازش شده: {len(self.data)}")

    def _clean_text(self, text):
        """تمیزسازی متن"""
        if not isinstance(text, str):
            return ""

        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[\n\r\t]', ' ', text)
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