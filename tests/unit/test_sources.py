"""Tests for news source modules."""

import pytest
from unittest.mock import patch, MagicMock

from ai_news_summarizer.sources.rss import RSSSource
from ai_news_summarizer.sources.scraper import WebScraperSource
from ai_news_summarizer.sources.api_client import APISource
from ai_news_summarizer.sources.local_file import LocalFileSource


class TestRSSSource:
    """Tests for RSSSource."""

    def test_validate_config_requires_url(self):
        """Test that URL is required."""
        source = RSSSource(name="test", url="")
        with pytest.raises(ValueError, match="RSS source requires 'url'"):
            source.validate_config({})

    def test_validate_config_passes_with_url(self):
        """Test validation passes with URL."""
        source = RSSSource(name="test", url="https://example.com/feed")
        assert source.validate_config({"url": "https://example.com/feed"})

    @pytest.mark.asyncio
    async def test_fetch_parses_entries(self, mock_rss_feed):
        """Test that fetch correctly parses RSS entries."""
        with patch("feedparser.parse") as mock_parse:
            mock_parse.return_value = mock_rss_feed

            source = RSSSource(name="test", url="https://example.com/feed")
            items = await source.fetch(max_items=10)

            assert len(items) == 2
            assert items[0].title == "Test Article 1"
            assert items[1].title == "Test Article 2"


class TestWebScraperSource:
    """Tests for WebScraperSource."""

    def test_validate_config_requires_url(self):
        """Test that URL is required."""
        source = WebScraperSource(name="test", url="")
        with pytest.raises(ValueError, match="WebScraper source requires 'url'"):
            source.validate_config({})


class TestAPISource:
    """Tests for APISource."""

    def test_validate_config_requires_endpoint(self):
        """Test that endpoint is required."""
        source = APISource(name="test", endpoint="")
        with pytest.raises(ValueError, match="API source requires 'endpoint'"):
            source.validate_config({})

    def test_validate_config_passes_with_endpoint(self):
        """Test validation passes with endpoint."""
        source = APISource(name="test", endpoint="https://api.example.com")
        assert source.validate_config({"endpoint": "https://api.example.com"})


class TestLocalFileSource:
    """Tests for LocalFileSource."""

    def test_validate_config_requires_path(self):
        """Test that file_path is required."""
        source = LocalFileSource(name="test", file_path="")
        with pytest.raises(ValueError, match="Local file source requires 'file_path'"):
            source.validate_config({})
