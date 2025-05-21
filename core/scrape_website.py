import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import re
from urllib.parse import urljoin, urlparse
import time
import logging

# تنظیم لاگینگ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_text(text):
    """پاکسازی متن از کاراکترهای اضافی"""
    if not isinstance(text, str):
        return ""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def is_valid_url(url, base_domain):
    """بررسی معتبر بودن URL"""
    try:
        parsed = urlparse(url)
        return parsed.netloc == base_domain and parsed.scheme in ['http', 'https']
    except:
        return False

def scrape_website(url, max_pages=100, output_file='output.json'):
    """
    خزش سایت و استخراج محتوا
    
    Args:
        url (str): آدرس سایت
        max_pages (int): حداکثر تعداد صفحات برای خزش
        output_file (str): مسیر فایل خروجی JSON
    
    Returns:
        bool: True در صورت موفقیت، False در صورت خطا
    """
    try:
        base_domain = urlparse(url).netloc
        visited_urls = set()
        to_visit = [url]
        pages_data = []
        
        logger.info(f"شروع خزش سایت: {url}")
        
        while to_visit and len(visited_urls) < max_pages:
            current_url = to_visit.pop(0)
            if current_url in visited_urls:
                continue
                
            try:
                logger.info(f"در حال خزش: {current_url}")
                response = requests.get(current_url, timeout=10)
                if response.status_code != 200:
                    continue
                    
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # استخراج عنوان و محتوا
                title = clean_text(soup.title.string if soup.title else '')
                content = clean_text(soup.get_text())
                
                # ذخیره داده‌های صفحه
                pages_data.append({
                    'url': current_url,
                    'title': title,
                    'content': content,
                    'timestamp': datetime.now().isoformat()
                })
                
                visited_urls.add(current_url)
                
                # یافتن لینک‌های جدید
                for link in soup.find_all('a', href=True):
                    new_url = urljoin(current_url, link['href'])
                    if is_valid_url(new_url, base_domain) and new_url not in visited_urls:
                        to_visit.append(new_url)
                        
                time.sleep(1)  # رعایت فاصله زمانی بین درخواست‌ها
                
            except Exception as e:
                logger.error(f"خطا در خزش {current_url}: {e}")
                continue
        
        # ذخیره نتایج در فایل JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(pages_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"خزش با موفقیت انجام شد. تعداد صفحات: {len(pages_data)}")
        return True
        
    except Exception as e:
        logger.error(f"خطا در خزش سایت: {e}")
        return False

if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else "https://parsicanada.com/"
    scrape_website(url) 