"""News source implementations."""

from ai_news_summarizer.sources.base import NewsSource
from ai_news_summarizer.sources.rss import RSSSource
from ai_news_summarizer.sources.scraper import WebScraperSource
from ai_news_summarizer.sources.api_client import APISource
from ai_news_summarizer.sources.local_file import LocalFileSource

__all__ = ["NewsSource", "RSSSource", "WebScraperSource", "APISource", "LocalFileSource"]
