"""FastAPI web application for AI News Summarizer."""

import json
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse

from ai_news_summarizer.core.processor import ProcessingResult
from ai_news_summarizer.core.service import AppService
from ai_news_summarizer.models.schemas import NewsItem
from ai_news_summarizer.sources.scraper import WebScraperSource


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "src" / "ai_news_summarizer" / "web" / "templates"
DATA_DIR = PROJECT_ROOT / "data"
HISTORY_PATH = DATA_DIR / "history.json"

env_path = PROJECT_ROOT / ".env"
if env_path.exists():
    load_dotenv(env_path)

app = FastAPI(title="AI News Summarizer", version="1.0.0")


def load_history() -> list[dict]:
    """Load persisted result history."""
    if not HISTORY_PATH.exists():
        return []
    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (json.JSONDecodeError, OSError):
        return []
    return data if isinstance(data, list) else []


def save_history_entry(entry: dict) -> None:
    """Append one history entry, keeping the file small."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    history = load_history()
    history.insert(0, entry)
    history = history[:50]
    with open(HISTORY_PATH, "w", encoding="utf-8") as handle:
        json.dump(history, handle, ensure_ascii=False, indent=2)


def find_latest_history() -> dict | None:
    """Return the newest saved batch result."""
    history = load_history()
    return history[0] if history else None


def search_history_entries(query: str, limit: int = 20) -> list[dict]:
    """Search saved summaries by summary text, URL, model, or source status."""
    normalized = query.strip().lower()
    if not normalized:
        return load_history()[:limit]

    matches: list[dict] = []
    for entry in load_history():
        haystack_parts: list[str] = [entry.get("created_at", "")]
        for result in entry.get("results", []):
            haystack_parts.extend(
                [
                    str(result.get("url") or ""),
                    str(result.get("summary") or ""),
                    str(result.get("model") or ""),
                    str(result.get("score") or ""),
                ]
            )
        for stat in entry.get("source_stats", []):
            haystack_parts.extend(
                [
                    str(stat.get("name") or ""),
                    str(stat.get("url") or ""),
                    str(stat.get("status") or ""),
                    str(stat.get("error") or ""),
                ]
            )
        if normalized in "\n".join(haystack_parts).lower():
            matches.append(entry)
            if len(matches) >= limit:
                break
    return matches


def filter_recent_items(items: list[NewsItem], max_hours: int) -> list[NewsItem]:
    """Keep recent items, while preserving items with no timestamp."""
    if max_hours <= 0:
        return items

    cutoff = datetime.now() - timedelta(hours=max_hours)
    filtered: list[NewsItem] = []
    for item in items:
        if item.published_at is None or item.published_at >= cutoff:
            filtered.append(item)
    return filtered


def dedupe_items(items: list[NewsItem]) -> list[NewsItem]:
    """Dedupe items by normalized title, then by URL."""
    seen_keys: set[str] = set()
    unique_items: list[NewsItem] = []
    for item in items:
        title_key = (item.title or "").strip().lower()
        url_key = str(item.url) if item.url else ""
        dedupe_key = url_key or title_key
        if not dedupe_key or dedupe_key in seen_keys:
            continue
        seen_keys.add(dedupe_key)
        unique_items.append(item)
    return unique_items


def serialize_result(result: ProcessingResult) -> dict:
    """Serialize a processing result for JSON responses."""
    return {
        "success": True,
        "created_at": datetime.now().isoformat(),
        "from_cache": False,
        "count": len(result.summaries),
        "total_fetched": result.total_fetched,
        "results": [
            {
                "url": str(item.original_url) if item.original_url else None,
                "summary": item.summary,
                "model": item.model,
                "tokens": item.token_usage or 0,
                "score": item.metadata.get("score"),
            }
            for item in result.summaries
        ],
        "source_stats": result.source_stats,
    }


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """Serve the main page."""
    template_path = TEMPLATES_DIR / "index.html"
    with open(template_path, "r", encoding="utf-8") as handle:
        html_content = handle.read()
    return HTMLResponse(content=html_content)


@app.post("/api/summarize")
async def summarize(
    sources_json: str = Form(...),
    provider: str = Form("openai"),
    max_hours: int = Form(72),
    max_items: int = Form(10),
) -> JSONResponse:
    """Run summarization and return JSON results."""
    import json

    try:
        raw_sources = json.loads(sources_json)
    except json.JSONDecodeError:
        return JSONResponse({"error": "Invalid sources JSON"}, status_code=400)

    config_path = PROJECT_ROOT / "config" / "default_config.yaml"
    full_config = AppService.load_config(config_path) if config_path.exists() else {}

    try:
        prepared = AppService.build_processor(
            full_config,
            provider_override=provider,
            raw_sources=raw_sources,
        )
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)

    processor = prepared.processor

    try:
        items, source_stats = await processor.fetch_all(max_items_per_source=max_items)
        filtered_items = filter_recent_items(items, max_hours)
        unique_items = dedupe_items(filtered_items)
        summaries = await processor.summarizer.summarize_batch(unique_items)
        result = ProcessingResult(
            summaries=summaries,
            source_stats=source_stats,
            total_fetched=len(items),
        )
        payload = serialize_result(result)
        payload["history_type"] = "batch"
        save_history_entry(payload)
        return JSONResponse(payload)
    except Exception as exc:
        err = str(exc).lower()
        if "429" in err or "rate limit" in err or "too many requests" in err:
            return JSONResponse(
                {"error": "LLM rate limit reached. Retry after 10-15 seconds or reduce the batch size."},
                status_code=429,
            )
        return JSONResponse({"error": str(exc)}, status_code=500)
    finally:
        await processor.close()


@app.post("/api/fetch-single")
async def fetch_single(url: str = Form(...), source_type: str = Form("scraper")) -> JSONResponse:
    """Fetch and summarize a single URL."""
    if source_type != "scraper":
        return JSONResponse({"error": "Only scraper mode is supported for single URL requests."}, status_code=400)

    source = WebScraperSource(name="single", url=url)
    prepared = None

    try:
        items = await source.fetch(max_items=1)
        if not items:
            return JSONResponse({"error": "No content found"}, status_code=404)

        config_path = PROJECT_ROOT / "config" / "default_config.yaml"
        full_config = AppService.load_config(config_path) if config_path.exists() else {}
        prepared = AppService.build_processor(full_config, provider_override=None, raw_sources=[])
        summary = await prepared.processor.summarizer.summarize(items[0])

        payload = {
            "success": True,
            "title": items[0].title,
            "url": str(items[0].url) if items[0].url else None,
            "content": items[0].content[:500] + "..." if len(items[0].content) > 500 else items[0].content,
            "summary": summary.summary,
            "model": summary.model,
            "tokens": summary.token_usage,
        }
        save_history_entry(
            {
                "success": True,
                "created_at": datetime.now().isoformat(),
                "from_cache": False,
                "history_type": "single",
                "count": 1,
                "total_fetched": 1,
                "results": [
                    {
                        "url": payload["url"],
                        "summary": payload["summary"],
                        "model": payload["model"],
                        "tokens": payload["tokens"] or 0,
                        "score": None,
                    }
                ],
                "source_stats": [
                    {
                        "name": "single",
                        "url": url,
                        "status": "success",
                        "count": 1,
                        "priority": 0,
                        "error": None,
                    }
                ],
            }
        )
        return JSONResponse(payload)
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)
    finally:
        await source.close()
        if prepared is not None:
            await prepared.processor.close()


@app.get("/api/history/latest")
async def latest_history() -> JSONResponse:
    """Return the latest saved result without fetching sources again."""
    entry = find_latest_history()
    if entry is None:
        return JSONResponse({"success": True, "count": 0, "results": [], "source_stats": [], "from_cache": True})
    cached = dict(entry)
    cached["from_cache"] = True
    return JSONResponse(cached)


@app.get("/api/history/search")
async def search_history(q: str = "", limit: int = 20) -> JSONResponse:
    """Search saved history entries."""
    entries = search_history_entries(q, limit=max(1, min(limit, 50)))
    return JSONResponse({"success": True, "count": len(entries), "entries": entries, "from_cache": True})


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
