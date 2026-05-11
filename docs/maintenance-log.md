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

## 2026-05-11

### Chinese UI and scoring pass

- Localized the main web experience to Chinese, including the history panel, source controls, run button, and empty states.
- Switched the visible app title and wordmark to a Chinese-facing brief format.
- Added score badges to result cards and single-item views so recommendation scores are visible everywhere.
- Kept score-based ordering in the UI, with source priority used as the tie-breaker.
- Removed the pre-summarized score prefix from AIHot summaries so the score is shown as a separate field instead of duplicated in the text.

### Source reliability pass

- Updated the default source set so Phoenix News uses an RSSHub-backed feed with fallback URLs.
- Updated Machine Heart to use its native RSS feed with a fallback URL.
- Added fallback feed support to the RSS source loader so a source can try multiple URLs before failing.
- Surface RSS source failures explicitly when a feed returns no items, which makes broken sources easier to spot in the UI.

### History and metadata pass

- Expanded saved history entries with source name, source priority, and pre-summarized flags.
- History search now considers source metadata in addition to URLs, summaries, models, and scores.
- Refresh still restores the latest saved result without refetching RSS.

### 2026-05-11 scoring recovery pass

- Removed the broken Phoenix News and Machine Heart RSS entries from the default source list and the sidebar UI.
- Kept only AIHot and IT之家 in the default starter set so the app boots cleanly without broken source noise.
- Changed the summarizer to emit and parse strict JSON for summary responses, which made score extraction much more reliable.
- Added a separate scoring prompt for pre-summarized sources so AIHot now gets a real score even when the feed itself does not provide one.
- Fixed the missing score normalization helpers that were breaking the new score path during runtime verification.

### 2026-05-11 README and screenshot polish

- Added `docs/assets/readme-example-homepage.png` as the GitHub example image for the current Chinese UI.
- Rewrote `README.md` into a clean Chinese overview with setup, run, history cache, Docker, and default source notes.
- Linked the README to the screenshot so the repository landing page now shows the finished UI state directly.

### 2026-05-11 RSS compatibility and lint cleanup

- Made `RSSSource` accept dict-like feed and entry objects so the mocked RSS fixtures used in tests work the same way as real `feedparser` output.
- Removed stale unused imports flagged by `ruff` in schemas, source base classes, scraper, and source tests.
- Re-ran the full local check loop after the fix: `compileall`, `pytest`, and `ruff check` all pass.

### 2026-05-11 README screenshot refresh

- Re-captured `docs/assets/readme-example-homepage.png` from the current local UI so the GitHub example image matches the latest score and summary layout.
- Expanded the README introduction to explain the scoring system and the LLM-generated summary flow more directly.
- Updated the screenshot alt text so the example image describes the scoring + summary view instead of only the generic homepage.
