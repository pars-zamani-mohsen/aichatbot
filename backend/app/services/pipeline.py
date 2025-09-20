import aiohttp
import asyncio
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import pandas as pd
from pathlib import Path
import logging
from typing import List, Dict, Any, Set
import json
# from sentence_transformers import SentenceTransformer
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
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'))

logger = logging.getLogger(__name__)

# تعریف مسیر پایه برای ChromaDB
CHROMA_BASE_DIR = Path("/var/www/html/ai/backend")

# خواندن مقدار MAX_PAGES از فایل .env
MAX_PAGES = int(os.getenv('MAX_PAGES', 100))  # مقدار پیش‌فرض 100 است

class WebCrawlerPipeline:
    def __init__(self, base_url: str, crawl_settings: Dict[str, Any] = None):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.visited_urls: Set[str] = set()
        self.data: List[Dict[str, Any]] = []
        self.base_dir = Path(__file__).parent.parent.parent
        self.output_dir = self.base_dir / "processed_data" / self.domain
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = None
        self.force_crawl_urls: Set[str] = set()  # URL هایی که باید force کراول شوند
        
        # تنظیمات کراولینگ
        self.crawl_settings = crawl_settings or {}
        self.max_pages = self.crawl_settings.get('max_pages', MAX_PAGES)
        self.max_depth = self.crawl_settings.get('max_depth', 3)
        self.delay = self.crawl_settings.get('delay', 1)  # تأخیر بین درخواست‌ها (ثانیه)
        self.respect_robots = self.crawl_settings.get('respect_robots', True)
        self.user_agent = self.crawl_settings.get('user_agent', 'RAG-Crawler/1.0')
        
        # robots.txt rules
        self.robots_rules = {
            'allowed': set(),
            'disallowed': set(),
            'crawl_delay': 1
        }
        
        if settings.DEBUG_MODE:
            logger.info(f"Output directory created at: {self.output_dir}")
            logger.info(f"Crawl settings: max_pages={self.max_pages}, max_depth={self.max_depth}, delay={self.delay}")
        
        # بارگذاری URL های موجود از CSV
        self._load_existing_urls()
    
    def _load_existing_urls(self):
        """بارگذاری URL های موجود از CSV"""
        csv_path = self.output_dir / "processed_data.csv"
        if csv_path.exists():
            try:
                df = pd.read_csv(csv_path)
                existing_urls = set(df['url'].tolist())
                self.visited_urls.update(existing_urls)
                logger.info(f"بارگذاری {len(existing_urls)} URL موجود از CSV")
            except Exception as e:
                logger.warning(f"خطا در بارگذاری URL های موجود: {e}")
    
    def add_force_crawl_url(self, url: str):
        """اضافه کردن URL به لیست force crawl"""
        self.force_crawl_urls.add(url)
        logger.info(f"URL {url} به لیست force crawl اضافه شد")
        
    def is_valid_url(self, url: str) -> bool:
        """بررسی معتبر بودن URL"""
        try:
            result = urlparse(url)
            # بررسی اینکه URL دارای scheme و netloc باشد
            if not all([result.scheme, result.netloc]):
                return False
            
            # بررسی اینکه domain با domain اصلی مطابقت داشته باشد
            if result.netloc != self.domain:
                return False
                
            # بررسی اینکه URL معتبر باشد
            if result.scheme not in ['http', 'https']:
                return False
                
            return True
        except Exception as e:
            logger.warning(f"خطا در بررسی URL {url}: {e}")
            return False
            
    def should_crawl(self, url: str) -> bool:
        """بررسی اینکه آیا باید URL را کراول کنیم یا خیر"""
        if url in self.visited_urls:
            return False
            
        parsed = urlparse(url)
        if parsed.netloc != self.domain:
            return False
        
        # بررسی robots.txt
        if not self.is_allowed_by_robots(url):
            return False
        
        # بررسی اینکه آیا URL قبلاً کراول شده یا نه
        # اگر URL در لیست force_crawl_urls است، اجازه کراولینگ بده
        if url in self.force_crawl_urls:
            logger.info(f"URL {url} در لیست force crawl است، کراول می‌شود")
            return True
        
        # اگر URL قبلاً کراول شده، نادیده بگیر
        if url in self.visited_urls:
            logger.info(f"URL {url} قبلاً کراول شده است، نادیده گرفته می‌شود")
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
        
        # بررسی حداکثر تعداد صفحات
        if len(self.visited_urls) >= self.max_pages:
            return False
                
        return True
    
    async def parse_robots_txt(self):
        """خواندن و تجزیه robots.txt"""
        if not self.respect_robots:
            return
            
        try:
            robots_url = f"http://{self.domain}/robots.txt"
            async with self.session.get(robots_url, headers={'User-Agent': self.user_agent}) as response:
                if response.status == 200:
                    content = await response.text()
                    self._parse_robots_content(content)
                    logger.info(f"Robots.txt loaded for {self.domain}")
        except Exception as e:
            logger.warning(f"Could not load robots.txt for {self.domain}: {str(e)}")
    
    def _parse_robots_content(self, content: str):
        """تجزیه محتوای robots.txt"""
        current_user_agent = None
        
        for line in content.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            if ':' in line:
                directive, value = line.split(':', 1)
                directive = directive.strip().lower()
                value = value.strip()
                
                if directive == 'user-agent':
                    current_user_agent = value
                elif directive == 'allow' and (current_user_agent == '*' or current_user_agent == self.user_agent):
                    self.robots_rules['allowed'].add(value)
                elif directive == 'disallow' and (current_user_agent == '*' or current_user_agent == self.user_agent):
                    self.robots_rules['disallowed'].add(value)
                elif directive == 'crawl-delay' and (current_user_agent == '*' or current_user_agent == self.user_agent):
                    try:
                        self.robots_rules['crawl_delay'] = float(value)
                    except ValueError:
                        pass
    
    def is_allowed_by_robots(self, url: str) -> bool:
        """بررسی اینکه آیا URL توسط robots.txt مجاز است"""
        if not self.respect_robots:
            return True
            
        path = urlparse(url).path
        
        # بررسی disallow rules
        for disallowed in self.robots_rules['disallowed']:
            if path.startswith(disallowed):
                return False
        
        # بررسی allow rules
        for allowed in self.robots_rules['allowed']:
            if path.startswith(allowed):
                return True
        
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
            # Rate limiting - تأخیر بین درخواست‌ها
            delay = max(self.delay, self.robots_rules['crawl_delay'])
            await asyncio.sleep(delay)
            
            # تنظیمات SSL و timeout
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            timeout = aiohttp.ClientTimeout(total=30)  # افزایش timeout به 30 ثانیه
            
            # تنظیم headers
            headers = {
                'User-Agent': self.user_agent,
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
                        href = link['href'].strip()
                        
                        # نادیده گرفتن لینک‌های خالی یا fragment-only
                        if not href or href.startswith('#'):
                            continue
                            
                        # تبدیل URL نسبی به مطلق
                        try:
                            absolute_url = urljoin(url, href)
                            
                            # بررسی معتبر بودن URL
                            if not self.is_valid_url(absolute_url):
                                continue
                                
                            # حذف fragment (#) از URL
                            clean_url = absolute_url.split('#')[0]
                            
                            # حذف پارامترهای اضافی
                            if '?' in clean_url:
                                base_url = clean_url.split('?')[0]
                                # فقط پارامترهای مهم را نگه می‌داریم
                                params = clean_url.split('?')[1]
                                important_params = []
                                for param in params.split('&'):
                                    if any(key in param.lower() for key in ['page', 'id', 'article', 'post']):
                                        important_params.append(param)
                                if important_params:
                                    clean_url = f"{base_url}?{'&'.join(important_params)}"
                                else:
                                    clean_url = base_url
                            
                            # اضافه کردن به لیست اگر تکراری نباشد
                            if clean_url not in links:
                                links.append(clean_url)
                                
                        except Exception as e:
                            logger.warning(f"خطا در پردازش لینک {href}: {e}")
                            continue
                            
                    return {
                        'url': url,
                        'title': title,
                        'text': text,
                        'links': links,
                        'source_type': 'website'  # Website crawling
                    }
                    
        except Exception as e:
            logger.error(f"خطا در کراول صفحه {url}: {str(e)}")
            # به جای raise کردن، None برگردانیم تا process_urls بتواند ادامه دهد
            return None
            
    async def process_urls(self, urls_to_crawl: List[str], pbar: tqdm):
        """پردازش همزمان URL‌ها"""
        tasks = []
        for url in urls_to_crawl:
            # بررسی معتبر بودن URL قبل از اضافه کردن به tasks
            if not self.is_valid_url(url):
                logger.warning(f"URL نامعتبر نادیده گرفته شد: {url}")
                pbar.update(1)
                continue
                
            if self.should_crawl(url):
                self.visited_urls.add(url)
                tasks.append(self.crawl_page(url))
                
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, dict) and result is not None:
                    self.data.append(result)
                    pbar.update(1)
                    pbar.set_description(f"صفحات پردازش شده: {len(self.data)}")
                elif isinstance(result, Exception):
                    logger.warning(f"خطا در پردازش URL: {str(result)}")
                    pbar.update(1)  # به‌روزرسانی progress bar حتی در صورت خطا
                elif result is None:
                    logger.warning(f"صفحه کراول نشد (نتیجه None)")
                    pbar.update(1)  # به‌روزرسانی progress bar حتی در صورت خطا
                    
    async def run_async(self) -> bool:
        """اجرای فرآیند کراول به صورت همزمان"""
        try:
            # ایجاد session
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            self.session = aiohttp.ClientSession(connector=connector)
            
            # خواندن robots.txt
            await self.parse_robots_txt()
            
            urls_to_crawl = [self.base_url]
            
            with tqdm(total=self.max_pages, desc="در حال کراول") as pbar:
                while urls_to_crawl and len(self.data) < self.max_pages:
                    batch_size = min(10, len(urls_to_crawl))  # پردازش 10 URL همزمان
                    current_batch = urls_to_crawl[:batch_size]
                    urls_to_crawl = urls_to_crawl[batch_size:]
                    
                    await self.process_urls(current_batch, pbar)
                    
                    # اضافه کردن لینک‌های جدید به صف
                    new_links = set()
                    for page_data in self.data:
                        if page_data and 'links' in page_data:
                            new_links.update(page_data['links'])
                    
                    # فیلتر کردن لینک‌های جدید
                    filtered_links = [link for link in new_links 
                                    if self.should_crawl(link) and link not in self.visited_urls]
                    urls_to_crawl.extend(filtered_links)
                    
                    # حذف تکرارها
                    urls_to_crawl = list(dict.fromkeys(urls_to_crawl))
            
            # بستن session
            await self.session.close()
            
            # ذخیره داده‌ها
            if self.data:
                df_new = pd.DataFrame(self.data)
                csv_path = self.output_dir / "processed_data.csv"
                
                # اگر فایل CSV موجود است، داده‌های جدید را به آن اضافه کن
                if csv_path.exists():
                    df_existing = pd.read_csv(csv_path)
                    # حذف ردیف‌های تکراری بر اساس URL
                    df_combined = pd.concat([df_existing, df_new], ignore_index=True)
                    df_combined = df_combined.drop_duplicates(subset=['url'], keep='last')
                    df_combined.to_csv(csv_path, index=False)
                    logger.info(f"تعداد صفحات جدید کراول شده: {len(self.data)}")
                    logger.info(f"تعداد کل صفحات: {len(df_combined)}")
                else:
                    # اگر فایل وجود ندارد، فایل جدید ایجاد کن
                    df_new.to_csv(csv_path, index=False)
                    logger.info(f"فایل جدید ایجاد شد با {len(self.data)} صفحه")
                
                return True
            else:
                logger.warning("هیچ داده‌ای کراول نشد")
                return True  # حتی اگر هیچ داده‌ای کراول نشود، موفق در نظر بگیریم
            
        except Exception as e:
            logger.error(f"خطا در اجرای کراول: {str(e)}")
            if self.session:
                await self.session.close()
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
                if settings.DEBUG_MODE:
                    logger.info(f"کالکشن قبلی {self.collection_name} حذف شد")
            except Exception:
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
            
            if settings.DEBUG_MODE:
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
        if settings.DEBUG_MODE:
            logger.info("در حال بارگذاری مدل امبدینگ...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        if settings.DEBUG_MODE:
            logger.info("مدل امبدینگ بارگذاری شد")
        
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """تولید امبدینگ برای متون"""
        if settings.DEBUG_MODE:
            logger.info(f"در حال تولید امبدینگ برای {len(texts)} متن...")
        embeddings = self.model.encode(texts, show_progress_bar=settings.DEBUG_MODE)
        if settings.DEBUG_MODE:
            logger.info("تولید امبدینگ با موفقیت انجام شد")
        return embeddings
        
    def run(self, new_urls_only: bool = True) -> bool:
        """اجرای فرآیند تولید امبدینگ و ایجاد knowledge base"""
        try:
            # خواندن داده‌ها
            csv_path = self.data_dir / "processed_data.csv"
            if not csv_path.exists():
                logger.error("فایل داده یافت نشد")
                return False
                
            if settings.DEBUG_MODE:
                logger.info("در حال خواندن فایل CSV...")
            df = pd.read_csv(csv_path)
            if settings.DEBUG_MODE:
                logger.info(f"تعداد رکوردهای خوانده شده: {len(df)}")
            
            # اگر فقط برای URL های جدید امبدینگ تولید کنیم
            if new_urls_only:
                # خواندن metadata موجود برای پیدا کردن URL های قبلی
                metadata_path = self.data_dir / "metadata.json"
                existing_urls = set()
                if metadata_path.exists():
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        existing_metadata = json.load(f)
                        existing_urls = {meta['url'] for meta in existing_metadata}
                
                # فیلتر کردن فقط ردیف‌های جدید
                df_new = df[~df['url'].isin(existing_urls)]
                if len(df_new) == 0:
                    logger.info("هیچ URL جدیدی برای تولید امبدینگ یافت نشد")
                    return True
                
                logger.info(f"تولید امبدینگ برای {len(df_new)} URL جدید")
                texts = df_new['text'].tolist()
                df_to_process = df_new
            else:
                # تولید امبدینگ برای همه ردیف‌ها
                texts = df['text'].tolist()
                df_to_process = df
            
            # تولید امبدینگ برای متن‌ها
            embeddings = self.generate_embeddings(texts)
            
            # ذخیره امبدینگ‌ها به صورت JSON (لیست لیست‌ها)
            if settings.DEBUG_MODE:
                logger.info("در حال ذخیره امبدینگ‌ها به صورت JSON...")
            embeddings_list = embeddings.tolist()
            
            # اگر فایل embeddings موجود است، آن را به‌روزرسانی کن
            embeddings_path = self.data_dir / "embeddings.json"
            if embeddings_path.exists():
                # خواندن امبدینگ‌های موجود
                with open(embeddings_path, 'r', encoding='utf-8') as f:
                    existing_embeddings = json.load(f)
                
                # اضافه کردن امبدینگ‌های جدید
                existing_embeddings.extend(embeddings_list)
                
                # حذف تکراری‌ها بر اساس URL
                # این کار پیچیده است، پس فعلاً همه را نگه می‌داریم
                with open(embeddings_path, 'w', encoding='utf-8') as f:
                    json.dump(existing_embeddings, f)
            else:
                with open(embeddings_path, 'w', encoding='utf-8') as f:
                    json.dump(embeddings_list, f)

            # ذخیره metadata هر سند (url, title, chunk_id, ...)
            if settings.DEBUG_MODE:
                logger.info("در حال ذخیره متادیتا...")
            metadata_list = []
            for i, row in df_to_process.iterrows():
                meta = {
                    'url': row.get('url', ''),
                    'title': row.get('title', ''),
                    'chunk_id': i,
                    'timestamp': row.get('timestamp', time.strftime('%Y-%m-%d %H:%M:%S'))
                }
                metadata_list.append(meta)
            
            # اگر فایل metadata موجود است، آن را به‌روزرسانی کن
            metadata_path = self.data_dir / "metadata.json"
            if metadata_path.exists():
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    existing_metadata = json.load(f)
                existing_metadata.extend(metadata_list)
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(existing_metadata, f, ensure_ascii=False, indent=2)
            else:
                with open(metadata_path, 'w', encoding='utf-8') as f:
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

            if settings.DEBUG_MODE:
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