"""Tests for the Summarizer class."""

import pytest

from ai_news_summarizer.core.summarizer import Summarizer


class TestSummarizer:
    """Tests for summarizer behavior."""

    @pytest.fixture
    def summarizer(self, mock_llm_client, summary_config):
        return Summarizer(mock_llm_client, summary_config)

    def test_build_prompt_includes_title(self, summarizer, sample_news_item):
        prompt = summarizer._build_prompt(sample_news_item)
        assert sample_news_item.title in prompt

    def test_build_prompt_excludes_title_when_disabled(self, summarizer, sample_news_item):
        summarizer.config.include_title = False
        prompt = summarizer._build_prompt(sample_news_item)
        assert f"Title: {sample_news_item.title}" not in prompt

    def test_build_prompt_respects_max_length(self, summarizer, sample_news_item):
        prompt = summarizer._build_prompt(sample_news_item)
        assert "摘要不超过 5 句话" in prompt

    def test_build_prompt_uses_configured_language(self, summarizer, sample_news_item):
        prompt = summarizer._build_prompt(sample_news_item)
        assert "请使用简体中文" in prompt

    @pytest.mark.asyncio
    async def test_summarize_returns_summary(self, summarizer, sample_news_item):
        result = await summarizer.summarize(sample_news_item)
        assert isinstance(result.summary, str)
        assert len(result.summary) > 0
        assert result.model == "test-model"

    @pytest.mark.asyncio
    async def test_summarize_includes_token_usage(self, summarizer, sample_news_item):
        result = await summarizer.summarize(sample_news_item)
        assert result.token_usage == 150

    @pytest.mark.asyncio
    async def test_summarize_batch_uses_generate_with_usage(self, summarizer, sample_news_items):
        results = await summarizer.summarize_batch(sample_news_items)
        assert len(results) == len(sample_news_items)
        assert summarizer.llm.generate_with_usage.await_count == len(sample_news_items)

    @pytest.mark.asyncio
    async def test_pre_summarized_item_gets_score_from_llm_when_missing(self, summarizer, sample_news_item):
        sample_news_item.metadata["pre_summarized"] = True
        sample_news_item.metadata.pop("score", None)
        summarizer.llm.generate_with_usage.return_value = ('{"score": 8.5}', 24)

        result = await summarizer.summarize(sample_news_item)

        assert result.score == 8.5
        assert result.summary == sample_news_item.content
        assert summarizer.llm.generate_with_usage.await_count == 1
