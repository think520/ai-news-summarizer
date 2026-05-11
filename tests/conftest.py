"""Pytest fixtures."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from ai_news_summarizer.llm.base import LLMClient
from ai_news_summarizer.models.schemas import NewsItem, Summary, SummaryConfig


@pytest.fixture
def sample_news_item():
    return NewsItem(
        id="test-001",
        title="Test article",
        content="This is a sample article body used to test summarization behavior.",
        url="https://example.com/article",
        source="test_source",
        metadata={"author": "Test Author"},
    )


@pytest.fixture
def sample_news_items():
    return [
        NewsItem(
            id=f"test-{i:03d}",
            title=f"Test article {i}",
            content=f"Body for article {i}.",
            url=f"https://example.com/article-{i}",
            source="test_source",
        )
        for i in range(1, 4)
    ]


@pytest.fixture
def sample_summary():
    return Summary(
        original_url="https://example.com/article",
        summary="Sample summary.",
        model="test-model",
        token_usage=100,
    )


@pytest.fixture
def summary_config():
    return SummaryConfig(
        max_length=5,
        style="concise",
        include_title=True,
        language="zh",
    )


@pytest.fixture
def mock_llm_client():
    client = MagicMock(spec=LLMClient)
    client.model_name = "test-model"
    client.provider_name = "test"
    client.generate = AsyncMock(return_value="Generated summary.")
    client.generate_with_usage = AsyncMock(return_value=("Generated summary.", 150))
    client.close = AsyncMock()
    return client


@pytest.fixture
def mock_rss_feed():
    return {
        "entries": [
            {
                "id": "article-1",
                "title": "Test Article 1",
                "link": "https://example.com/article-1",
                "summary": "This is the summary of article 1.",
                "published_parsed": (2024, 1, 15, 12, 0, 0, 0, 0, 0),
                "author": "Test Author",
                "tags": [{"term": "tech"}],
            },
            {
                "id": "article-2",
                "title": "Test Article 2",
                "link": "https://example.com/article-2",
                "summary": "This is the summary of article 2.",
                "published_parsed": (2024, 1, 14, 12, 0, 0, 0, 0, 0),
                "author": "Test Author",
                "tags": [{"term": "news"}],
            },
        ]
    }
