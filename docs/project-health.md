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

## Known issues not fixed yet

### Product and data model gaps

- No persistence layer for fetched items, summaries, or cost history.
- No incremental fetch mode or "new since last run" workflow.
- No unified task model for long-running web requests.

### Source quality gaps

- Scraper extraction is still selector-based and fragile for complex sites.
- Deduplication is still simple and should evolve toward canonical URL plus content hashing.

### UX and presentation gaps

- The main web template contains encoding corruption and needs a full UTF-8 cleanup pass.
- User-facing HTML and in-browser reporting remain lightly structured.

### Suggested next steps

1. Add SQLite-backed persistence for fetched items, summaries, and run history.
2. Move web summarization into background jobs with status polling.
3. Introduce stronger dedupe keys and incremental fetch semantics.
4. Normalize the front-end template encoding and copy.
