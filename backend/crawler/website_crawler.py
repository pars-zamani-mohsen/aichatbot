from urllib.parse import urljoin, urlparse
import aiohttp
import asyncio
from bs4 import BeautifulSoup
from typing import Set, List, Dict
import logging

class WebsiteCrawler:
    def __init__(self):
        self.visited_urls: Set[str] = set()
        self.data: List[Dict] = []
        self.base_url: str = ""

    async def crawl(self, domain: str, max_pages: int = 100) -> List[Dict]:
        self.base_url = f"https://{domain}" if not domain.startswith(('http://', 'https://')) else domain
        async with aiohttp.ClientSession() as session:
            await self._crawl_page(session, self.base_url, max_pages)
        return self.data

    async def _crawl_page(self, session: aiohttp.ClientSession, url: str, max_pages: int) -> None:
        if len(self.visited_urls) >= max_pages or url in self.visited_urls:
            return

        try:
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    # استخراج محتوا
                    content = self._extract_content(soup)
                    if content:
                        self.data.append({
                            'url': url,
                            'title': soup.title.string if soup.title else '',
                            'content': content
                        })

                    self.visited_urls.add(url)

                    # پیدا کردن لینک‌های جدید
                    links = soup.find_all('a', href=True)
                    tasks = []
                    for link in links:
                        href = link['href']
                        if href.startswith('/'):
                            href = urljoin(self.base_url, href)
                        if self._is_valid_url(href):
                            tasks.append(self._crawl_page(session, href, max_pages))

                    if tasks:
                        await asyncio.gather(*tasks)

        except Exception as e:
            logging.error(f"Error crawling {url}: {str(e)}")

    def _extract_content(self, soup: BeautifulSoup) -> str:
        # حذف اسکریپت‌ها و استایل‌ها
        for script in soup(['script', 'style', 'nav', 'footer']):
            script.decompose()

        # استخراج متن از تگ‌های مهم
        content_tags = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'li', 'article'])
        content = ' '.join(tag.get_text().strip() for tag in content_tags)
        return content

    def _is_valid_url(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
            return (
                parsed.netloc.endswith(urlparse(self.base_url).netloc) and
                parsed.scheme in ('http', 'https')
            )
        except:
            return False