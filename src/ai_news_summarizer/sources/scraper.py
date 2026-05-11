"""Web scraping news source."""

from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from ai_news_summarizer.models.schemas import NewsItem
from ai_news_summarizer.sources.base import NewsSource


class WebScraperSource(NewsSource):
    """Web page scraping news source."""

    def __init__(
        self,
        name: str,
        url: str,
        title_selector: str = "h1, h2",
        content_selector: str = "article, .content, .post-content, main",
        link_selector: str = "a",
        max_items: int = 10,
        **kwargs,
    ):
        super().__init__(
            name,
            url=url,
            title_selector=title_selector,
            content_selector=content_selector,
            link_selector=link_selector,
            max_items=max_items,
            **kwargs,
        )
        self.url = url
        self.title_selector = title_selector
        self.content_selector = content_selector
        self.link_selector = link_selector
        self.max_items = max_items

    def validate_config(self, config: dict) -> bool:
        """Validate scraper source configuration."""
        if "url" not in config:
            raise ValueError("WebScraper source requires 'url' parameter")
        return True

    async def fetch(self, **kwargs) -> list[NewsItem]:
        """Fetch news items by scraping a web page."""
        max_items = kwargs.get("max_items", self.max_items)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(self.url)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")

        items = []
        articles = soup.select(self.content_selector)[:max_items]

        for i, article in enumerate(articles):
            title_elem = article.select_one(self.title_selector)
            title = title_elem.get_text(strip=True) if title_elem else f"Article {i + 1}"

            content = article.get_text(separator="\n", strip=True)

            link_elem = article.select_one(self.link_selector)
            link = urljoin(self.url, link_elem.get("href", "")) if link_elem else self.url

            item = NewsItem(
                id=f"{self.name}-{i}",
                title=title,
                content=content[:5000],
                url=link,
                source=self.name,
                metadata={"scraped_url": self.url},
            )
            items.append(item)

        return items
