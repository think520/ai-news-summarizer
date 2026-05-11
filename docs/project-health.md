# Project Health

## Fixed in the current pass

### High priority

- CLI and core return contract drift:
  - `NewsProcessor.process()` now returns a structured `ProcessingResult`.
  - CLI and web both consume the same shared assembly path.

- Config default-provider drift:
  - The application now resolves the default model provider from `llm.default`.

- Duplicate entry-point assembly:
  - Provider/source construction now lives in `core/service.py`.

- Resource cleanup gaps:
  - Summarizer and LLM clients now expose cleanup hooks used by processor shutdown.

- Test drift:
  - Core integration and summarizer tests were rewritten to match actual async behavior.

- Documentation and GitHub preview:
  - README now includes the current Chinese UI screenshot from `docs/assets/readme-example-homepage.png`.
  - The repository homepage can show the finished interface state directly through the embedded image.

## Known issues not fixed yet

### Product and data model gaps

- No persistence layer for fetched items, summaries, or cost history.
- No incremental fetch mode or "new since last run" workflow.
- No unified task model for long-running web requests.

### Source quality gaps

- Scraper extraction is still selector-based and fragile for complex sites.
- Deduplication is still simple and should evolve toward canonical URL plus content hashing.
- The default source list has been trimmed to the two reliable starters, but the app still needs a replacement RSS discovery workflow for richer coverage.

### UX and presentation gaps

- The main web template has been localized, but some legacy comments and non-user-facing fragments still carry encoding noise.
- User-facing HTML and in-browser reporting are improved, but the next useful step is richer per-card metadata and history filters.

### Suggested next steps

1. Add SQLite-backed persistence for fetched items, summaries, and run history.
2. Move web summarization into background jobs with status polling.
3. Introduce stronger dedupe keys and incremental fetch semantics.
4. Add per-card actions such as favorite, read, and ignore.
5. Add a source-management panel that can validate and preview new RSS subscriptions before saving them.
