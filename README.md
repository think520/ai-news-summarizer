# AI News Summarizer

AI News Summarizer is a lightweight personal news intelligence dashboard. It pulls from RSS, web pages, APIs, or local files, then summarizes or displays curated items through a CLI and a FastAPI web UI.

The current default setup gives `AIHot` the highest priority. That feed is already curated by a large model, so the app treats it as pre-summarized, preserves its score when available, and avoids a second LLM call for those entries.

## Features

- Multi-source ingestion: RSS, scraper, API, local files
- Multi-provider LLM support: OpenAI-compatible APIs, Anthropic, Ollama
- AIHot-aware priority and score sorting
- Local history cache so page refreshes do not refetch RSS
- History search API and web-side search panel
- CLI and FastAPI web entry points

## Requirements

- Python 3.11+
- `uv`
- An LLM API key if you want to summarize non-pre-summarized sources

## Setup

```powershell
uv sync --dev
Copy-Item .env.example .env
```

Edit `.env` and set your keys:

```env
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
```

The default OpenAI-compatible provider in `config/default_config.yaml` points at MiniMax:

```yaml
llm:
  default: "openai"
  providers:
    openai:
      model: "MiniMax-M2.7"
      base_url: "https://api.minimax.chat/v1"
```

## Run Locally

Web UI:

```powershell
uv run uvicorn ai_news_summarizer.web.app:app --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

CLI:

```powershell
uv run ai-news summarize -c ./config/default_config.yaml
```

## History Cache

Successful runs are saved to:

```text
data/history.json
```

This file is intentionally ignored by Git. On page load, the web app calls:

```text
GET /api/history/latest
```

So refreshing the page restores the latest result without pulling feeds again. Search uses:

```text
GET /api/history/search?q=keyword
```

## Docker

Build:

```powershell
docker build -t ai-news-summarizer .
```

Run:

```powershell
docker run --rm -p 8000:8000 --env-file .env -v ${PWD}/data:/app/data ai-news-summarizer
```

Then open:

```text
http://127.0.0.1:8000
```

## Configuration

Sources live in `config/default_config.yaml`.

Example high-priority pre-summarized source:

```yaml
sources:
  - type: "rss"
    name: "aihot_virxact"
    params:
      url: "https://aihot.virxact.com/feed.xml"
      max_items: 20
      priority: 100
      pre_summarized: true
```

Items are sorted by source priority first, then by extracted recommendation score.

## GitHub Safety Notes

Do not commit:

- `.env`
- `.venv/`
- `.uv-cache/`
- `data/history.json`
- generated reports such as `results.html`

The included `.gitignore` handles these by default.

## Project Docs

- `docs/maintenance-log.md` records major implementation changes.
- `docs/project-health.md` tracks known issues and recommended next steps.
