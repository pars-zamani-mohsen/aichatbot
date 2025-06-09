import aiohttp
import asyncio
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import pandas as pd
from pathlib import Path
import logging
from typing import List, Dict, Any, Set
import json
from sentence_transformers import SentenceTransformer
import numpy as np
from tqdm import tqdm
import time
from tenacity import retry, stop_after_attempt, wait_exponential
import ssl
import os
from dotenv import load_dotenv
import chromadb
from app.config import settings

# بارگذاری متغیرهای محیطی
load_dotenv()

logger = logging.getLogger(__name__)

# تعریف مسیر پایه برای ChromaDB
CHROMA_BASE_DIR = Path("/var/www/html/ai/backend")

# خواندن مقدار MAX_PAGES از فایل .env
MAX_PAGES = int(os.getenv('MAX_PAGES', 100))  # مقدار پیش‌فرض 100 است

class WebCrawlerPipeline:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.visited_urls: Set[str] = set()
        self.data: List[Dict[str, Any]] = []
        self.base_dir = Path(__file__).parent.parent.parent
        self.output_dir = self.base_dir / "processed_data" / self.domain
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = None
        logger.info(f"Output directory created at: {self.output_dir}")
        
    def is_valid_url(self, url: str) -> bool:
        """بررسی معتبر بودن URL"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
            
    def should_crawl(self, url: str) -> bool:
        """بررسی اینکه آیا باید URL را کراول کنیم یا خیر"""
        if url in self.visited_urls:
            return False
            
        parsed = urlparse(url)
        if parsed.netloc != self.domain:
            return False
            
        # حذف URL‌های با پسوندهای خاص
        excluded_extensions = [
            '.pdf', '.jpg', '.jpeg', '.png', '.gif', '.css', '.js', 
            '.mp4', '.mp3', '.wav', '.avi', '.mov', '.wmv', '.flv',
            '.zip', '.rar', '.7z', '.doc', '.docx', '.xls', '.xlsx',
            '.ppt', '.pptx', '.xml', '.json', '.ico', '.svg', '.woff',
            '.woff2', '.ttf', '.eot', '.otf', '.webp'
        ]
        
        # بررسی پسوند فایل
        path = parsed.path.lower()
        if any(path.endswith(ext) for ext in excluded_extensions):
            return False
            
        # بررسی پارامترهای URL
        if '?' in url:
            query = url.split('?')[1].lower()
            if any(ext in query for ext in excluded_extensions):
                return False
                
        return True
        
    def extract_text(self, soup: BeautifulSoup) -> str:
        """استخراج متن از صفحه"""
        # حذف تگ‌های script و style
        for script in soup(["script", "style"]):
            script.decompose()
            
        # استخراج متن
        text = soup.get_text(separator=' ', strip=True)
        
        # حذف خطوط خالی و فضاهای اضافی
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=20))
    async def crawl_page(self, url: str) -> Dict[str, Any]:
        """کراول کردن یک صفحه با retry و timeout"""
        try:
            # تنظیمات SSL و timeout
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            timeout = aiohttp.ClientTimeout(total=30)  # افزایش timeout به 30 ثانیه
            
            # تنظیم headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url, timeout=timeout, headers=headers) as response:
                    if response.status != 200:
                        logger.warning(f"خطا در دریافت صفحه {url}: کد {response.status}")
                        return None
                        
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # استخراج عنوان
                    title = soup.title.string if soup.title else ""
                    
                    # استخراج متن
                    text = self.extract_text(soup)
                    
                    # استخراج لینک‌ها
                    links = []
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        absolute_url = urljoin(url, href)
                        if self.is_valid_url(absolute_url):
                            links.append(absolute_url)
                            
                    return {
                        'url': url,
                        'title': title,
                        'text': text,
                        'links': links
                    }
                    
        except Exception as e:
            logger.error(f"خطا در کراول صفحه {url}: {str(e)}")
            raise
            
    async def process_urls(self, urls_to_crawl: List[str], pbar: tqdm):
        """پردازش همزمان URL‌ها"""
        tasks = []
        for url in urls_to_crawl:
            if self.should_crawl(url):
                self.visited_urls.add(url)
                tasks.append(self.crawl_page(url))
                
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, dict):
                    self.data.append(result)
                    pbar.update(1)
                    pbar.set_description(f"صفحات پردازش شده: {len(self.data)}")
                    
    async def run_async(self) -> bool:
        """اجرای فرآیند کراول به صورت همزمان"""
        try:
            urls_to_crawl = [self.base_url]
            
            with tqdm(total=MAX_PAGES, desc="در حال کراول") as pbar:
                while urls_to_crawl and len(self.data) < MAX_PAGES:
                    batch_size = min(10, len(urls_to_crawl))  # پردازش 10 URL همزمان
                    current_batch = urls_to_crawl[:batch_size]
                    urls_to_crawl = urls_to_crawl[batch_size:]
                    
                    await self.process_urls(current_batch, pbar)
                    
                    # اضافه کردن لینک‌های جدید به صف
                    new_links = set()
                    for page_data in self.data:
                        new_links.update(page_data['links'])
                    urls_to_crawl.extend([link for link in new_links 
                                        if self.should_crawl(link)])
            
            # ذخیره داده‌ها
            if self.data:
                df = pd.DataFrame(self.data)
                df.to_csv(self.output_dir / "processed_data.csv", index=False)
                logger.info(f"تعداد صفحات کراول شده: {len(self.data)}")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"خطا در اجرای کراول: {str(e)}")
            return False
            
    def run(self) -> bool:
        """اجرای فرآیند کراول"""
        return asyncio.run(self.run_async())

class KnowledgeBasePipeline:
    def __init__(self, domain: str):
        self.domain = domain
        self.base_dir = Path(__file__).parent.parent.parent
        self.data_dir = self.base_dir / "processed_data" / domain
        self.collection_name = domain  # استفاده مستقیم از دامنه بدون تبدیل نقطه به آندرلاین
        self.chroma_dir = self.base_dir / "knowledge_base" / domain  # مسیر مخصوص برای هر سایت
        
    def run(self) -> bool:
        """ایجاد knowledge base از امبدینگ‌ها و متادیتا"""
        try:
            logger.info("در حال ایجاد knowledge base...")
            
            # خواندن امبدینگ‌ها
            embeddings_path = self.data_dir / "embeddings.json"
            if not embeddings_path.exists():
                logger.error("فایل امبدینگ‌ها یافت نشد")
                return False
                
            with open(embeddings_path, 'r') as f:
                embeddings = json.load(f)
                
            # خواندن متادیتا
            metadata_path = self.data_dir / "metadata.json"
            if not metadata_path.exists():
                logger.error("فایل متادیتا یافت نشد")
                return False
                
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                
            # خواندن داده‌های اصلی
            csv_path = self.data_dir / "processed_data.csv"
            if not csv_path.exists():
                logger.error("فایل داده یافت نشد")
                return False
                
            df = pd.read_csv(csv_path)
            
            # ایجاد پوشه ChromaDB برای سایت
            self.chroma_dir.mkdir(parents=True, exist_ok=True)
            
            # ایجاد کلاینت ChromaDB
            client = chromadb.PersistentClient(path=str(self.chroma_dir))
            
            # حذف کالکشن قبلی با همین نام (اگر وجود داشت)
            try:
                client.delete_collection(self.collection_name)
                logger.info(f"کالکشن قبلی {self.collection_name} حذف شد")
            except:
                pass
            
            # ایجاد کالکشن جدید
            collection = client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
            # آماده‌سازی داده‌ها
            documents = []
            for i, row in df.iterrows():
                title = row.get('title', '')
                text = row.get('text', '')
                documents.append(f"{title}\n\n{text}")
            
            # اضافه کردن داده‌ها به collection
            collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=metadata,
                ids=[str(i) for i in range(len(embeddings))]
            )
            
            logger.info(f"Knowledge base با موفقیت ایجاد شد. نام collection: {self.collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"خطا در ایجاد knowledge base: {str(e)}")
            return False

class EmbeddingPipeline:
    def __init__(self, domain: str):
        self.domain = domain
        self.base_dir = Path(__file__).parent.parent.parent
        self.data_dir = self.base_dir / "processed_data" / domain
        logger.info("در حال بارگذاری مدل امبدینگ...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("مدل امبدینگ بارگذاری شد")
        
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """تولید امبدینگ برای متون"""
        logger.info(f"در حال تولید امبدینگ برای {len(texts)} متن...")
        embeddings = self.model.encode(texts, show_progress_bar=True)
        logger.info("تولید امبدینگ با موفقیت انجام شد")
        return embeddings
        
    def run(self) -> bool:
        """اجرای فرآیند تولید امبدینگ و ایجاد knowledge base"""
        try:
            # خواندن داده‌ها
            csv_path = self.data_dir / "processed_data.csv"
            if not csv_path.exists():
                logger.error("فایل داده یافت نشد")
                return False
                
            logger.info("در حال خواندن فایل CSV...")
            df = pd.read_csv(csv_path)
            logger.info(f"تعداد رکوردهای خوانده شده: {len(df)}")
            
            # تولید امبدینگ برای متن‌ها
            texts = df['text'].tolist()
            embeddings = self.generate_embeddings(texts)
            
            # ذخیره امبدینگ‌ها به صورت JSON (لیست لیست‌ها)
            logger.info("در حال ذخیره امبدینگ‌ها به صورت JSON...")
            embeddings_list = embeddings.tolist()
            with open(self.data_dir / "embeddings.json", 'w', encoding='utf-8') as f:
                json.dump(embeddings_list, f)

            # ذخیره metadata هر سند (url, title, chunk_id, ...)
            logger.info("در حال ذخیره متادیتا...")
            metadata_list = []
            for i, row in df.iterrows():
                meta = {
                    'url': row.get('url', ''),
                    'title': row.get('title', ''),
                    'chunk_id': i,
                    'timestamp': row.get('timestamp', time.strftime('%Y-%m-%d %H:%M:%S'))
                }
                metadata_list.append(meta)
            with open(self.data_dir / "metadata.json", 'w', encoding='utf-8') as f:
                json.dump(metadata_list, f, ensure_ascii=False, indent=2)

            # ذخیره اطلاعات مدل (اختیاری)
            model_info = {
                'model_name': 'all-MiniLM-L6-v2',
                'embedding_size': int(embeddings.shape[1]),
                'num_documents': len(df),
                'columns': df.columns.tolist()
            }
            with open(self.data_dir / "model_info.json", 'w', encoding='utf-8') as f:
                json.dump(model_info, f, ensure_ascii=False, indent=2)

            logger.info("فرآیند امبدینگ با موفقیت به پایان رسید")
            
            # ایجاد knowledge base
            kb_pipeline = KnowledgeBasePipeline(self.domain)
            if not kb_pipeline.run():
                logger.error("خطا در ایجاد knowledge base")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"خطا در تولید امبدینگ: {str(e)}")
            return False 