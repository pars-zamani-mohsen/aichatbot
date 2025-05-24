from celery import Celery
from sqlalchemy.orm import Session
from ..database.database import SessionLocal
from ..database import models
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin, urlparse
import pandas as pd
import time
import logging
from ..config import settings
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import re
from typing import List, Set, Dict, Optional

# تنظیمات Celery
celery = Celery('crawler', broker=settings.REDIS_URL)
celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Tehran',
    enable_utc=True
)

# تنظیمات لاگینگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WebCrawlerPipeline:
    def __init__(
        self,
        start_url: str,
        max_pages: int = 100,
        allowed_domains: Optional[List[str]] = None,
        excluded_paths: Optional[List[str]] = None
    ):
        self.start_url = start_url
        self.max_pages = max_pages
        self.allowed_domains = allowed_domains or [urlparse(start_url).netloc]
        self.excluded_paths = excluded_paths or []
        self.visited_urls = set()
        self.data = []
        
    def _is_valid_url(self, url: str) -> bool:
        """بررسی معتبر بودن URL"""
        try:
            parsed = urlparse(url)
            return (
                parsed.scheme in ['http', 'https'] and
                parsed.netloc in self.allowed_domains and
                not any(path in parsed.path for path in self.excluded_paths)
            )
        except Exception:
            return False
            
    def _extract_text(self, soup: BeautifulSoup) -> str:
        """استخراج متن از HTML"""
        # حذف تگ‌های ناخواسته
        for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
            tag.decompose()
            
        # استخراج متن
        text = soup.get_text(separator=' ', strip=True)
        
        # پاکسازی متن
        text = ' '.join(text.split())
        
        return text
        
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """استخراج لینک‌ها از HTML"""
        links = []
        for a in soup.find_all('a', href=True):
            url = urljoin(base_url, a['href'])
            if self._is_valid_url(url):
                links.append(url)
        return links
        
    def crawl_page(self, url: str) -> Optional[Dict]:
        """کراول کردن یک صفحه"""
        try:
            # بررسی URL تکراری
            if url in self.visited_urls:
                return None
                
            # اضافه کردن به URL‌های بازدید شده
            self.visited_urls.add(url)
            
            # دریافت صفحه با timeout بیشتر
            response = requests.get(url, timeout=30)  # افزایش timeout به 30 ثانیه
            response.raise_for_status()
            
            # پارس کردن HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # استخراج عنوان
            title = soup.title.string if soup.title else ''
            
            # استخراج متن
            text = self._extract_text(soup)
            
            # استخراج لینک‌ها
            links = self._extract_links(soup, url)
            
            return {
                'url': url,
                'title': title,
                'text': text,
                'links': links
            }
            
        except Exception as e:
            logger.error(f"خطا در کراول کردن {url}: {str(e)}")
            return None
            
    def crawl(self) -> pd.DataFrame:
        """شروع کراول کردن"""
        urls_to_visit = [self.start_url]
        
        while urls_to_visit and len(self.visited_urls) < self.max_pages:
            url = urls_to_visit.pop(0)
            
            # کراول کردن صفحه
            page_data = self.crawl_page(url)
            if page_data:
                self.data.append(page_data)
                urls_to_visit.extend(page_data['links'])
                
        # تبدیل به DataFrame
        df = pd.DataFrame(self.data)
        return df
        
    def save_to_csv(self, file_path: str):
        """ذخیره نتایج در CSV"""
        df = self.crawl()
        df.to_csv(file_path, index=False, encoding='utf-8')
        logger.info(f"نتایج در {file_path} ذخیره شد")

@celery.task
def crawl_website_task(start_url: str, output_file: str):
    """تسک Celery برای کراول کردن وب‌سایت"""
    try:
        crawler = WebCrawlerPipeline(start_url)
        crawler.save_to_csv(output_file)
        return {"status": "success", "file": output_file}
    except Exception as e:
        logger.error(f"خطا در تسک کراول: {str(e)}")
        return {"status": "error", "message": str(e)}

@celery.task
def start_crawling(website_id: int):
    """شروع کراولینگ برای یک سایت"""
    db = SessionLocal()
    try:
        # دریافت اطلاعات سایت
        website = db.query(models.Website).filter(models.Website.id == website_id).first()
        if not website:
            logger.error(f"سایت با شناسه {website_id} یافت نشد")
            return
        
        # به‌روزرسانی وضعیت
        website.status = "crawling"
        db.commit()
        
        try:
            # شروع کراولینگ
            crawler = WebCrawlerPipeline(website.url)
            data = crawler.crawl()
            
            # ایجاد مسیر کامل برای ذخیره فایل
            base_dir = Path(__file__).parent.parent.parent
            save_dir = base_dir / "processed_data" / website.domain
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # ذخیره داده‌ها
            df = pd.DataFrame(data)
            df.to_csv(save_dir / "crawled_data.csv", index=False)
            
            # به‌روزرسانی اطلاعات کراولینگ
            website.crawl_info = {
                'total_pages': len(data),
                'crawled_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            website.status = "processing"
            db.commit()
            
            # شروع پردازش داده‌ها
            from .embedding import process_website
            process_website.delay(website_id)
            
        except Exception as e:
            logger.error(f"خطا در کراولینگ سایت {website.url}: {str(e)}")
            website.status = "error"
            website.error_message = str(e)
            db.commit()
            
    finally:
        db.close() 