"""RSS/Atom feed news source."""

import feedparser
import re
from datetime import datetime

from ai_news_summarizer.models.schemas import NewsItem
from ai_news_summarizer.sources.base import NewsSource


class RSSSource(NewsSource):
    """RSS/Atom feed news source."""

    def __init__(
        self,
        name: str,
        url: str,
        max_items: int = 20,
        priority: int = 0,
        pre_summarized: bool = False,
        **kwargs,
    ):
        super().__init__(name, url=url, max_items=max_items, **kwargs)
        self.url = url
        self.max_items = max_items
        self.priority = priority
        self.pre_summarized = pre_summarized

    def validate_config(self, config: dict) -> bool:
        """Validate RSS source configuration."""
        if "url" not in config:
            raise ValueError("RSS source requires 'url' parameter")
        return True

    async def fetch(self, **kwargs) -> list[NewsItem]:
        """Fetch news items from an RSS/Atom feed."""
        max_items = kwargs.get("max_items", self.max_items)

        feed = feedparser.parse(self.url)

        items = []
        for entry in feed.entries[:max_items]:
            # Skip entries without title or link
            entry_title = getattr(entry, "title", None) or getattr(entry, "title_detail", None)
            entry_link = getattr(entry, "link", None)
            if not entry_title or not entry_link:
                continue

            content = ""
            if hasattr(entry, "summary"):
                content = entry.summary
            elif hasattr(entry, "content") and entry.content:
                content = entry.content[0].value if entry.content[0] else ""
            elif hasattr(entry, "description"):
                content = entry.description or ""

            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                try:
                    published = datetime(*entry.published_parsed[:6])
                except Exception:
                    pass

            entry_id = getattr(entry, "id", None) or entry_link or f"rss-{hash(entry_link)}"

            item = NewsItem(
                id=entry_id,
                title=str(entry_title),
                content=str(content) if content else "",
                url=entry_link,
                source=self.name,
                published_at=published,
                metadata={
                    "author": entry.get("author", "") or "",
                    "tags": [tag.term for tag in getattr(entry, "tags", [])] if hasattr(entry, "tags") else [],
                    "priority": self.priority,
                    "pre_summarized": self.pre_summarized,
                    "score": self._extract_score(entry, str(content)),
                },
            )
            items.append(item)

        items.sort(key=lambda item: item.metadata.get("score") or 0, reverse=True)
        return items

    def _extract_score(self, entry, content: str) -> float | None:
        """Extract recommendation scores from common RSS fields."""
        candidates = [
            entry.get("score"),
            entry.get("rating"),
            entry.get("recommendation_score"),
            entry.get("recommend_score"),
            entry.get("ai_score"),
            entry.get("value_score"),
        ]

        for candidate in candidates:
            score = self._coerce_score(candidate)
            if score is not None:
                return score

        haystack = "\n".join(
            str(part)
            for part in (
                getattr(entry, "title", ""),
                getattr(entry, "summary", ""),
                content,
            )
            if part
        )
        patterns = [
            r"(?:score|rating|recommendation|recommend|推荐|评分|精选分|价值分)\D{0,12}(\d+(?:\.\d+)?)",
            r"(\d+(?:\.\d+)?)\s*(?:/|／)\s*100",
            r"(\d+(?:\.\d+)?)\s*(?:分|points?)",
        ]
        for pattern in patterns:
            match = re.search(pattern, haystack, flags=re.IGNORECASE)
            if match:
                return self._coerce_score(match.group(1))

        return None

    @staticmethod
    def _coerce_score(value) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            match = re.search(r"\d+(?:\.\d+)?", str(value))
            return float(match.group(0)) if match else None
