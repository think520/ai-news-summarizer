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
        fallback_urls: list[str] | None = None,
        max_items: int = 20,
        priority: int = 0,
        pre_summarized: bool = False,
        **kwargs,
    ):
        super().__init__(name, url=url, max_items=max_items, **kwargs)
        self.url = url
        self.fallback_urls = fallback_urls or []
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

        feed = None
        feed_url = None
        last_error: str | None = None
        for candidate_url in [self.url, *self.fallback_urls]:
            candidate_feed = feedparser.parse(candidate_url)
            candidate_entries = self._get_feed_entries(candidate_feed)
            if candidate_entries:
                feed = candidate_feed
                feed_url = candidate_url
                break
            if self._get_field(candidate_feed, "bozo", False):
                bozo_exc = self._get_field(candidate_feed, "bozo_exception", None)
                if bozo_exc is not None:
                    last_error = str(bozo_exc)

        if feed is None:
            detail = f": {last_error}" if last_error else ""
            raise RuntimeError(f"No feed items found for RSS source '{self.name}'{detail}")

        items = []
        for entry in self._get_feed_entries(feed)[:max_items]:
            # Skip entries without title or link
            entry_title = self._get_field(entry, "title") or self._get_field(entry, "title_detail")
            entry_link = self._get_field(entry, "link")
            if not entry_title or not entry_link:
                continue

            content = ""
            summary = self._get_field(entry, "summary")
            content_list = self._get_field(entry, "content", [])
            description = self._get_field(entry, "description")
            if summary:
                content = summary
            elif content_list:
                first_content = content_list[0]
                if isinstance(first_content, dict):
                    content = first_content.get("value", "")
                else:
                    content = getattr(first_content, "value", "") or ""
            elif description:
                content = description or ""

            published = None
            published_parsed = self._get_field(entry, "published_parsed")
            if published_parsed:
                try:
                    published = datetime(*published_parsed[:6])
                except Exception:
                    pass

            entry_id = self._get_field(entry, "id") or entry_link or f"rss-{hash(entry_link)}"
            tags = self._get_field(entry, "tags", []) or []

            item = NewsItem(
                id=entry_id,
                title=str(entry_title),
                content=str(content) if content else "",
                url=entry_link,
                source=self.name,
                published_at=published,
                metadata={
                    "author": self._get_field(entry, "author", "") or "",
                    "tags": [
                        tag.get("term", "") if isinstance(tag, dict) else getattr(tag, "term", "")
                        for tag in tags
                    ],
                    "priority": self.priority,
                    "pre_summarized": self.pre_summarized,
                    "score": self._extract_score(entry, str(content)),
                    "feed_url": feed_url or self.url,
                },
            )
            items.append(item)

        items.sort(key=lambda item: item.metadata.get("score") or 0, reverse=True)
        return items

    def _extract_score(self, entry, content: str) -> float | None:
        """Extract a normalized 0-10 recommendation score from RSS fields or text."""
        candidates = [
            self._get_field(entry, "score"),
            self._get_field(entry, "rating"),
            self._get_field(entry, "recommendation_score"),
            self._get_field(entry, "recommend_score"),
            self._get_field(entry, "ai_score"),
            self._get_field(entry, "value_score"),
            self._get_field(entry, "rank_score"),
            self._get_field(entry, "hot_score"),
        ]

        for candidate in candidates:
            score = self._normalize_score(self._coerce_score(candidate))
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
            r"(?:score|rating|recommendation|recommend)\D{0,12}(\d+(?:\.\d+)?)",
            r"(\d+(?:\.\d+)?)\s*(?:/|／)\s*10",
            r"(\d+(?:\.\d+)?)\s*(?:/|／)\s*100",
            r"(\d+(?:\.\d+)?)\s*(?:points?|pts?)",
        ]
        for pattern in patterns:
            match = re.search(pattern, haystack, flags=re.IGNORECASE)
            if match:
                score = self._normalize_score(self._coerce_score(match.group(1)))
                if score is not None:
                    return score

        return None

    @staticmethod
    def _get_feed_entries(feed) -> list:
        if isinstance(feed, dict):
            return feed.get("entries", []) or []
        return getattr(feed, "entries", []) or []

    @staticmethod
    def _get_field(entry, key: str, default=None):
        if isinstance(entry, dict):
            return entry.get(key, default)
        getter = getattr(entry, "get", None)
        if callable(getter):
            try:
                return getter(key, default)
            except TypeError:
                pass
        return getattr(entry, key, default)

    @staticmethod
    def _normalize_score(value: float | None) -> float | None:
        if value is None:
            return None
        if value > 10:
            value = value / 10 if value <= 100 else 10
        return max(0.0, min(10.0, value))

    @staticmethod
    def _coerce_score(value) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            match = re.search(r"\d+(?:\.\d+)?", str(value))
            return float(match.group(0)) if match else None
