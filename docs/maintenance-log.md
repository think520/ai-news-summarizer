# Maintenance Log

## 2026-04-30

### Structural fixes completed

- Added a shared assembly layer in `src/ai_news_summarizer/core/service.py` so CLI and web now resolve config, provider, and sources through the same path.
- Replaced the loose `process()` tuple contract with `ProcessingResult` in `src/ai_news_summarizer/core/processor.py`.
- Updated CLI to consume the structured result and to honor `llm.default` from config.
- Updated web handlers to reuse the shared service layer instead of rebuilding provider/source logic inline.
- Added model cleanup through `Summarizer.close()` and client `close()` methods for OpenAI and Anthropic adapters.
- Fixed environment-variable substitution so embedded patterns like `${HOST}/v1` now resolve correctly.
- Rewrote the most broken tests to match the current contracts and async call paths.
- Cleaned `CLAUDE.md` so it matches the actual Python project instead of the stale Node template.

### Remaining follow-ups

- The web template still contains encoding damage and should be normalized to UTF-8 in a dedicated pass.
- Source deduplication is still lightweight and should move beyond title-only logic over time.
- The project still lacks persistence, incremental fetch support, and task-based background execution.

## 2026-05-11

### AIHot source priority handling

- Added `https://aihot.virxact.com/feed.xml` as the first RSS source in `config/default_config.yaml`.
- Marked AIHot with `priority: 100` and `pre_summarized: true` because the feed is already curated by an LLM.
- Added RSS score extraction for common score/rating/recommendation fields and Chinese score labels.
- Sorted fetched items by source priority first, then recommendation score.
- For pre-summarized sources, summaries now reuse the source-provided content and skip an extra LLM call.
- Updated the web default source list so AIHot appears first in the UI.

### Result history cache

- Added local result persistence at `data/history.json`.
- Successful batch summarization and single-URL summarization now save a history entry.
- Added `GET /api/history/latest` so the web page can restore the latest result after refresh without pulling RSS again.
- Added `GET /api/history/search?q=...` for searching saved summaries, links, sources, model names, and scores.
- Updated the web page to auto-load the latest saved result on page load and added a small history search panel.

### GitHub deployment preparation

- Added `.gitignore` to keep secrets, virtual environments, caches, and runtime history out of Git.
- Added `.dockerignore` and `Dockerfile` for container-based deployment.
- Added GitHub Actions CI at `.github/workflows/ci.yml`.
- Added `README.md` with setup, run, Docker, configuration, history-cache, and safety instructions.
- Added `data/.gitkeep` so the runtime data directory exists without committing cached history.
- Added `docs/roadmap-and-deployment-plan.md` to collect recommended product direction, engineering roadmap, and deployment phases.
