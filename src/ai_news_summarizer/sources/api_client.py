"""API-based news source."""

from typing import Any, Optional

import httpx

from ai_news_summarizer.models.schemas import NewsItem
from ai_news_summarizer.sources.base import NewsSource


class APISource(NewsSource):
    """Generic API-based news source."""

    def __init__(
        self,
        name: str,
        endpoint: str,
        api_key: Optional[str] = None,
        params: Optional[dict] = None,
        max_items: int = 20,
        headers: Optional[dict] = None,
        **kwargs,
    ):
        super().__init__(
            name,
            endpoint=endpoint,
            api_key=api_key,
            params=params or {},
            max_items=max_items,
            headers=headers or {},
            **kwargs,
        )
        self.endpoint = endpoint
        self.api_key = api_key
        self.params = params or {}
        self.max_items = max_items
        self.headers = headers or {}

    def validate_config(self, config: dict) -> bool:
        """Validate API source configuration."""
        if "endpoint" not in config:
            raise ValueError("API source requires 'endpoint' parameter")
        return True

    async def fetch(self, **kwargs) -> list[NewsItem]:
        """Fetch news items from an API endpoint."""
        max_items = kwargs.get("max_items", self.max_items)
        params = {**self.params, **kwargs}

        headers = {**self.headers}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(self.endpoint, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()

        items = self._parse_response(data, max_items)
        return items

    def _parse_response(self, data: Any, max_items: int) -> list[NewsItem]:
        """Parse API response into NewsItem objects.

        Override this method for custom API formats.
        """
        items = []

        articles = data if isinstance(data, list) else data.get("articles", [])
        articles = articles[:max_items]

        for i, article in enumerate(articles):
            if isinstance(article, dict):
                item = NewsItem(
                    id=article.get("id", f"{self.name}-{i}"),
                    title=article.get("title", "Untitled"),
                    content=article.get("content", article.get("description", "")),
                    url=article.get("url"),
                    source=self.name,
                    published_at=article.get("publishedAt"),
                    metadata=article,
                )
                items.append(item)

        return items
