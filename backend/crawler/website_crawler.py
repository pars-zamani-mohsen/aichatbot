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

class WebsiteCrawler:
    def __init__(self, customer_manager: CustomerManager):
        self.customer_manager = customer_manager
        self.visited_urls = set()
        self.max_pages = 100
        self.logger = logging.getLogger(__name__)

        # Create SSL context that skips verification if needed
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

        # Session config with SSL settings
        self.session_config = {
            'connector': aiohttp.TCPConnector(ssl=self.ssl_context),
            'timeout': aiohttp.ClientTimeout(total=30)
        }

    async def crawl(self, domain: str, customer_id: str):
        """Crawl website and store content"""
        try:
            # Update status to running
            self.customer_manager.update_crawl_status(
                customer_id=customer_id,
                status="running"
            )

            base_url = f"https://{domain}" if not domain.startswith(('http://', 'https://')) else domain
            await self._crawl_page(base_url, domain)

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

    def _is_media_url(self, url: str) -> bool:
        """Check if URL points to media file"""
        extensions = {
            '.jpg', '.jpeg', '.png', '.gif',
            '.webp', '.svg', '.ico', '.bmp', '.tiff'
        }
        return any(url.lower().endswith(ext) for ext in extensions)

    async def _crawl_page(self, url: str, domain: str):
        """Crawl single page and extract content"""
        if len(self.visited_urls) >= self.max_pages or url in self.visited_urls:
            return

        try:
            self.visited_urls.add(url)
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract and store content
            content = self._extract_content(soup)
            if content:
                # Store content using customer manager
                pass

            # Find and crawl links
            links = self._extract_links(soup, domain)
            for link in links:
                if link not in self.visited_urls:
                    await self._crawl_page(link, domain)

        except Exception as e:
            self.logger.error(f"Error crawling {url}: {str(e)}")


    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract relevant content from page"""
        # Remove unwanted elements
        for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
            tag.decompose()

        # Get text content
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        return ' '.join(chunk for chunk in chunks if chunk)

    def _extract_links(self, soup: BeautifulSoup, domain: str) -> set:
        """Extract valid internal links"""
        links = set()
        for link in soup.find_all('a'):
            href = link.get('href')
            if href:
                absolute_url = urljoin(domain, href)
                if urlparse(absolute_url).netloc == urlparse(domain).netloc:
                    links.add(absolute_url)
        return links

    def _is_valid_url(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
            return (
                parsed.netloc.endswith(urlparse(self.base_url).netloc) and
                parsed.scheme in ('http', 'https')
            )
        except:
            return False