"""News processor orchestration."""

from dataclasses import dataclass
from typing import Any

from ai_news_summarizer.core.summarizer import Summarizer
from ai_news_summarizer.llm.base import LLMClient
from ai_news_summarizer.models.schemas import NewsItem, SourceConfig, Summary, SummaryConfig
from ai_news_summarizer.sources.api_client import APISource
from ai_news_summarizer.sources.base import NewsSource
from ai_news_summarizer.sources.local_file import LocalFileSource
from ai_news_summarizer.sources.rss import RSSSource
from ai_news_summarizer.sources.scraper import WebScraperSource


@dataclass(slots=True)
class ProcessingResult:
    """Structured result for a processor run."""

    summaries: list[Summary]
    source_stats: list[dict[str, Any]]
    total_fetched: int


class NewsProcessor:
    """Orchestrates news fetching and summarization."""

    SOURCE_CLASSES = {
        "rss": RSSSource,
        "scraper": WebScraperSource,
        "api": APISource,
        "local": LocalFileSource,
    }

    def __init__(self, sources: list[NewsSource], summarizer: Summarizer):
        self.sources = sources
        self.summarizer = summarizer

    @classmethod
    def from_config(
        cls,
        sources_config: list[SourceConfig],
        llm_client: LLMClient,
        summary_config: SummaryConfig,
    ) -> "NewsProcessor":
        """Create a processor from source and model configuration."""
        sources: list[NewsSource] = []
        for cfg in sources_config:
            source_class = cls.SOURCE_CLASSES.get(cfg.type)
            if source_class is None:
                raise ValueError(f"Unknown source type: {cfg.type}")
            sources.append(source_class(name=cfg.name, **cfg.params))

        summarizer = Summarizer(llm_client, summary_config)
        return cls(sources=sources, summarizer=summarizer)

    async def fetch_all(self, max_items_per_source: int = 10) -> tuple[list[NewsItem], list[dict[str, Any]]]:
        """Fetch items from all configured sources."""
        all_items: list[NewsItem] = []
        source_stats: list[dict[str, Any]] = []

        for source in self.sources:
            try:
                items = await source.fetch(max_items=max_items_per_source)
                all_items.extend(items)
                source_stats.append(
                    {
                        "name": source.name,
                        "url": getattr(source, "url", "") or "",
                        "status": "success",
                        "count": len(items),
                        "priority": getattr(source, "priority", 0),
                        "error": None,
                    }
                )
            except Exception as exc:
                source_stats.append(
                    {
                        "name": source.name,
                        "url": getattr(source, "url", "") or "",
                        "status": "error",
                        "count": 0,
                        "priority": getattr(source, "priority", 0),
                        "error": str(exc),
                    }
                )

        all_items.sort(
            key=lambda item: (
                item.metadata.get("priority") or 0,
                item.metadata.get("score") or 0,
            ),
            reverse=True,
        )
        return all_items, source_stats

    async def process(self, max_items_per_source: int = 10) -> ProcessingResult:
        """Fetch items and summarize them."""
        items, source_stats = await self.fetch_all(max_items_per_source)
        summaries = await self.summarizer.summarize_batch(items)
        return ProcessingResult(
            summaries=summaries,
            source_stats=source_stats,
            total_fetched=len(items),
        )

    async def process_single(self, news_item: NewsItem) -> Summary:
        """Generate a summary for one item."""
        return await self.summarizer.summarize(news_item)

    async def close(self) -> None:
        """Clean up source and model resources."""
        for source in self.sources:
            await source.close()
        await self.summarizer.close()
