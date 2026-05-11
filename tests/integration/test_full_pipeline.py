"""Integration tests for the main pipeline."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from ai_news_summarizer.core.processor import NewsProcessor, ProcessingResult
from ai_news_summarizer.core.summarizer import Summarizer
from ai_news_summarizer.models.schemas import SummaryConfig
from ai_news_summarizer.sources.rss import RSSSource


class TestFullPipeline:
    """Integration tests for the full fetch-to-summary path."""

    @pytest.fixture
    def mock_source(self, sample_news_items):
        source = MagicMock(spec=RSSSource)
        source.name = "test_source"
        source.fetch = AsyncMock(return_value=sample_news_items)
        source.close = AsyncMock()
        return source

    @pytest.fixture
    def mock_llm(self):
        client = MagicMock()
        client.model_name = "test-model"
        client.provider_name = "test"
        client.generate_with_usage = AsyncMock(return_value=("summary text", 100))
        client.close = AsyncMock()
        return client

    @pytest.mark.asyncio
    async def test_process_single_source(self, mock_source, mock_llm):
        summarizer = Summarizer(mock_llm, SummaryConfig())
        processor = NewsProcessor(sources=[mock_source], summarizer=summarizer)

        result = await processor.process(max_items_per_source=10)

        assert isinstance(result, ProcessingResult)
        assert len(result.summaries) == 3
        assert result.total_fetched == 3
        mock_source.fetch.assert_called_once_with(max_items=10)
        assert mock_llm.generate_with_usage.await_count == 3

    @pytest.mark.asyncio
    async def test_process_multiple_sources(self, sample_news_items, mock_llm):
        source1 = MagicMock(spec=RSSSource)
        source1.name = "source1"
        source1.fetch = AsyncMock(return_value=sample_news_items[:2])
        source1.close = AsyncMock()

        source2 = MagicMock(spec=RSSSource)
        source2.name = "source2"
        source2.fetch = AsyncMock(return_value=sample_news_items[2:])
        source2.close = AsyncMock()

        summarizer = Summarizer(mock_llm, SummaryConfig())
        processor = NewsProcessor(sources=[source1, source2], summarizer=summarizer)

        result = await processor.process(max_items_per_source=10)

        assert len(result.summaries) == 3
        assert result.total_fetched == 3
        assert len(result.source_stats) == 2

    @pytest.mark.asyncio
    async def test_process_handles_fetch_error(self, mock_llm):
        source = MagicMock(spec=RSSSource)
        source.name = "failing_source"
        source.fetch = AsyncMock(side_effect=Exception("Network error"))
        source.close = AsyncMock()

        summarizer = Summarizer(mock_llm, SummaryConfig())
        processor = NewsProcessor(sources=[source], summarizer=summarizer)

        result = await processor.process(max_items_per_source=10)

        assert result.summaries == []
        assert result.total_fetched == 0
        assert result.source_stats[0]["status"] == "error"

    @pytest.mark.asyncio
    async def test_process_single_item(self, sample_news_item, mock_llm):
        summarizer = Summarizer(mock_llm, SummaryConfig())
        processor = NewsProcessor(sources=[], summarizer=summarizer)

        result = await processor.process_single(sample_news_item)

        assert result.summary == "summary text"
        assert result.model == "test-model"
        mock_llm.generate_with_usage.assert_awaited_once()
