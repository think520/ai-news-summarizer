"""Local file news source."""

import json
from pathlib import Path
from typing import Optional

from ai_news_summarizer.models.schemas import NewsItem
from ai_news_summarizer.sources.base import NewsSource


class LocalFileSource(NewsSource):
    """Local file-based news source (JSON, TXT, Markdown)."""

    def __init__(
        self,
        name: str,
        file_path: str,
        format: str = "auto",
        max_items: int = 50,
        **kwargs,
    ):
        super().__init__(
            name,
            file_path=file_path,
            format=format,
            max_items=max_items,
            **kwargs,
        )
        self.file_path = Path(file_path)
        self.format = format.lower()
        self.max_items = max_items

    def validate_config(self, config: dict) -> bool:
        """Validate local file source configuration."""
        if "file_path" not in config:
            raise ValueError("Local file source requires 'file_path' parameter")
        path = Path(config["file_path"])
        if not path.exists():
            raise ValueError(f"File not found: {path}")
        return True

    async def fetch(self, **kwargs) -> list[NewsItem]:
        """Fetch news items from local files."""
        max_items = kwargs.get("max_items", self.max_items)

        if self.file_path.is_dir():
            return await self._fetch_from_directory(max_items)
        else:
            return await self._fetch_single_file(max_items)

    async def _fetch_from_directory(self, max_items: int) -> list[NewsItem]:
        """Fetch from all files in a directory."""
        items = []
        for file_path in self.file_path.glob("*"):
            if len(items) >= max_items:
                break
            file_items = await self._fetch_single_file(max_items - len(items), file_path)
            items.extend(file_items)
        return items

    async def _fetch_single_file(self, max_items: int, file_path: Optional[Path] = None) -> list[NewsItem]:
        """Fetch from a single file."""
        path = file_path or self.file_path
        suffix = path.suffix.lower()

        if suffix == ".json":
            return await self._parse_json(path, max_items)
        elif suffix in {".txt", ".md", ".markdown"}:
            return await self._parse_text(path, max_items)
        else:
            return []

    async def _parse_json(self, path: Path, max_items: int) -> list[NewsItem]:
        """Parse JSON file into NewsItems."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        items = []
        articles = data if isinstance(data, list) else data.get("articles", data.get("items", []))
        articles = articles[:max_items]

        for i, article in enumerate(articles):
            if isinstance(article, dict):
                item = NewsItem(
                    id=article.get("id", f"{self.name}-{path.stem}-{i}"),
                    title=article.get("title", "Untitled"),
                    content=article.get("content", article.get("body", "")),
                    url=article.get("url"),
                    source=self.name,
                    published_at=article.get("published_at", article.get("date")),
                    metadata=article,
                )
                items.append(item)

        return items

    async def _parse_text(self, path: Path, max_items: int) -> list[NewsItem]:
        """Parse text/markdown file into a single NewsItem."""
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        item = NewsItem(
            id=f"{self.name}-{path.stem}",
            title=path.stem,
            content=content[:10000],
            url=None,
            source=self.name,
            metadata={"file_path": str(path)},
        )
        return [item]
