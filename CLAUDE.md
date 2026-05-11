# CLAUDE.md

This file provides guidance for agents working in this repository.

## Project Overview

AI News Summarizer is a Python async news aggregation and summarization tool with:

- multiple source types: RSS, scraper, API, and local files
- multiple LLM providers: OpenAI-compatible, Anthropic, and Ollama
- CLI and FastAPI web entry points

## Commands

```bash
uv sync
uv sync --dev

ai-news --help
ai-news summarize -c ./config/default_config.yaml
ai-news web --reload

.venv\Scripts\python.exe -m pytest tests -q
.venv\Scripts\python.exe -m ruff check src tests
.venv\Scripts\python.exe -m mypy src
```

## Architecture

Pipeline:

```text
ConfigLoader
  -> AppService
  -> NewsProcessor
  -> Sources
  -> Summarizer
  -> LLM client
```

Key modules:

- `src/ai_news_summarizer/core/service.py`
  - shared assembly for CLI and web
- `src/ai_news_summarizer/core/processor.py`
  - fetch + summarize orchestration
- `src/ai_news_summarizer/core/summarizer.py`
  - prompt construction and output cleanup
- `src/ai_news_summarizer/sources/`
  - source strategies
- `src/ai_news_summarizer/llm/`
  - LLM adapters

## Notes

- Keep CLI and web behavior aligned through `AppService`; do not duplicate provider/source setup.
- Prefer structured return models over raw tuples or ad hoc dicts.
- Configuration defaults live under `llm.default`, not `default_llm`.
- This repository is Python-only. Ignore any old Node.js template assumptions.
