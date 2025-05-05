
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
