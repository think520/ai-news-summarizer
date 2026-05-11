"""Abstract base class for news sources."""

from abc import ABC, abstractmethod
from typing import Optional

from ai_news_summarizer.models.schemas import NewsItem


class NewsSource(ABC):
    """Abstract base class for all news sources."""

    def __init__(self, name: str, **kwargs):
        self.name = name
        self.config = kwargs

    @abstractmethod
    async def fetch(self, **kwargs) -> list[NewsItem]:
        """Fetch news items from this source.

        Args:
            **kwargs: Source-specific fetch parameters (e.g., max_items, url).

        Returns:
            List of NewsItem objects.
        """
        pass

    @abstractmethod
    def validate_config(self, config: dict) -> bool:
        """Validate that the source configuration is correct.

        Args:
            config: Configuration dictionary.

        Returns:
            True if valid, raises ValueError otherwise.
        """
        pass

    async def close(self):
        """Clean up resources (override if needed)."""
        pass
