import ssl
import aiohttp
import logging
import asyncio
import requests
from datetime import datetime
from models.customer import CustomerManager
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from typing import Set, List, Dict
import re
from collections import defaultdict
import nltk
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
import json
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
import time
from uuid import uuid4

class WebsiteCrawler:
    def __init__(self, customer_manager: CustomerManager):
        self.customer_manager = customer_manager
        self.visited_urls = set()
        self.max_pages = 100
        self.logger = logging.getLogger(__name__)
        self.page_priority = defaultdict(int)
        self.content_data = []
        
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
        
        # Download required NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords')

        # Create SSL context that skips verification if needed
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

        # Session config with SSL settings
        self.session_config = {
            'connector': aiohttp.TCPConnector(ssl=self.ssl_context),
            'timeout': aiohttp.ClientTimeout(total=30)
        }

    def get_priority_score(self, url: str) -> int:
        """تعیین اولویت URL"""
        url_lower = url.lower()
        for i, pattern in enumerate(self.priority_patterns):
            if pattern in url_lower:
                return i
        return len(self.priority_patterns)

    async def crawl(self, domain: str, customer_id: str):
        """Crawl website and store content"""
        try:
            # Update status to running
            self.customer_manager.update_crawl_status(
                customer_id=customer_id,
                status="running"
            )

            base_url = f"https://{domain}" if not domain.startswith(('http://', 'https://')) else domain
            
            # Create site directory
            site_dir = Path('processed_data') / domain
            site_dir.mkdir(parents=True, exist_ok=True)
            
            # Start parallel crawling
            await self._parallel_crawl(base_url, domain)
            
            # Save processed data
            self._save_processed_data(site_dir)
            
            # Update status to completed
            self.customer_manager.update_crawl_status(
                customer_id=customer_id,
                status="completed",
                crawled_at=datetime.now().isoformat()
            )

        except Exception as e:
            self.logger.error(f"Crawling error for {domain}: {str(e)}")
            # Update status to failed
            self.customer_manager.update_crawl_status(
                customer_id=customer_id,
                status="failed"
            )

    async def _parallel_crawl(self, base_url: str, domain: str):
        """Parallel crawling with priority"""
        to_visit = [(base_url, 0)]  # (url, depth)
        max_workers = 10  # تعداد threads همزمان

        self.logger.info(f"Starting parallel crawl from {base_url}")
        self.logger.info(f"Number of concurrent threads: {max_workers}")

        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Connection': 'keep-alive'
        })

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            while to_visit and len(self.visited_urls) < self.max_pages:
                # Sort URLs by priority
                to_visit.sort(key=lambda x: (self.get_priority_score(x[0]), x[1]))

                # Select URLs for parallel processing
                current_batch = []
                while to_visit and len(current_batch) < max_workers:
                    url, depth = to_visit.pop(0)
                    clean_url = self._clean_url(url)
                    if clean_url not in self.visited_urls:
                        current_batch.append((clean_url, depth))
                        self.visited_urls.add(clean_url)

                if not current_batch:
                    continue

                # Execute parallel requests
                future_to_url = {
                    executor.submit(self._process_page, session, url, depth): (url, depth)
                    for url, depth in current_batch
                }

                # Collect results
                for future in concurrent.futures.as_completed(future_to_url):
                    url, depth = future_to_url[future]
                    try:
                        result = future.result()
                        if result:
                            self.content_data.append(result['data'])
                            # Add new URLs
                            for new_url in result.get('new_urls', []):
                                clean_new_url = self._clean_url(new_url)
                                if clean_new_url not in self.visited_urls:
                                    to_visit.append((clean_new_url, depth + 1))
                    except Exception as e:
                        self.logger.error(f"Error processing {url}: {str(e)}")

                time.sleep(0.1)

        self.logger.info(f"Crawl completed - Pages processed: {len(self.content_data)}")
        self.logger.info(f"Total URLs visited: {len(self.visited_urls)}")

    def _clean_url(self, url: str) -> str:
        """Normalize URL"""
        parsed = urlparse(url)
        # Remove fragment and query
        cleaned = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        # Remove trailing slash
        return cleaned.rstrip('/')

    def _process_page(self, session: requests.Session, url: str, depth: int) -> Dict:
        """Process a single page"""
        # Check URL extension
        ignored_extensions = (
            '.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.ico', '.bmp', '.tiff',
            '.mp4', '.webm', '.ogg', '.mp3', '.wav', '.avi', '.mov', '.wmv',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.css', '.js', '.map', '.json', '.xml',
            '.ttf', '.woff', '.woff2', '.eot',
            '.zip', '.rar', '.tar', '.gz',
            '.php', '.aspx', '.ashx'
        )

        if url.lower().endswith(ignored_extensions):
            return None

        clean_url = self._clean_url(url)
        try:
            # HTTP request
            response = session.get(clean_url, timeout=10)
            response.raise_for_status()

            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            if not content_type.startswith('text/html'):
                return None

            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Collect new links
            new_urls = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                absolute_url = urljoin(url, href)
                parsed_url = urlparse(absolute_url)
                # Only same domain links
                if parsed_url.netloc == urlparse(url).netloc:
                    new_urls.append(absolute_url)

            # Remove irrelevant tags
            for tag in soup(['script', 'style', 'iframe', 'noscript']):
                tag.decompose()

            # Extract title
            title = soup.title.string if soup.title else ''

            # Extract content
            content = ""
            main_content = soup.find(['main', 'article', '#content', '.content', '[role="main"]'])
            if main_content:
                content = main_content.get_text(separator=' ', strip=True)
            else:
                body = soup.find('body')
                if body:
                    content = body.get_text(separator=' ', strip=True)

            # Clean content
            content = self._clean_text(content)

            if len(content) > 100:  # Minimum 100 characters
                chunk = {
                    'url': url,
                    'title': self._clean_text(title),
                    'content': content,
                    'chunk_id': f"{len(self.content_data)}_{int(time.time())}_{uuid4().hex[:8]}",
                    'timestamp': datetime.now().isoformat()
                }

                self.logger.info(f"Successfully processed {url} - {len(content)} characters")
                return {
                    'data': chunk,
                    'new_urls': new_urls
                }

            self.logger.warning(f"Rejected {url} - Invalid or duplicate content")
            return None

        except Exception as e:
            self.logger.error(f"Error fetching {url}: {str(e)}")
            return None

    def _clean_text(self, text: str) -> str:
        """Clean text"""
        if not isinstance(text, str):
            return ""

        # Remove special characters
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)

        # Remove extra spaces
        text = re.sub(r'\s+', ' ', text)

        # Remove empty lines
        text = re.sub(r'\n\s*\n', '\n', text)

        # Final cleanup
        return text.strip()

    def _save_processed_data(self, site_dir: Path):
        """Save processed data to files"""
        if not self.content_data:
            self.logger.warning("No data collected!")
            return False

        try:
            # Update crawl info
            crawl_info = {
                'total_pages': len(self.visited_urls),
                'total_content_items': len(self.content_data),
                'crawl_date': datetime.now().isoformat(),
                'page_priorities': dict(self.page_priority)
            }

            # Save crawl info
            with open(site_dir / 'crawl_info.json', 'w', encoding='utf-8') as f:
                json.dump(crawl_info, f, ensure_ascii=False, indent=2)

            # Save content data
            with open(site_dir / 'processed_data.json', 'w', encoding='utf-8') as f:
                json.dump(self.content_data, f, ensure_ascii=False, indent=2)

            self.logger.info(f"Results saved for {site_dir.name}")
            self.logger.info(f"Processed pages: {len(self.content_data)}")
            self.logger.info(f"Output path: {site_dir}")

            return True

        except Exception as e:
            self.logger.error(f"Error saving results: {str(e)}")
            return False