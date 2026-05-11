# Roadmap and Deployment Plan

This document collects the recommended next steps for turning the current project from a local AI news summarizer into a deployable personal AI intelligence dashboard.

## Current Position

The project already has a useful base:

- RSS, scraper, API, and local file sources
- OpenAI-compatible, Anthropic, and Ollama LLM adapters
- FastAPI web UI and CLI entry points
- AIHot as the highest-priority pre-summarized source
- Recommendation score extraction and priority-based sorting
- Local result history cache
- GitHub-ready project files: README, Dockerfile, CI, `.gitignore`, `.dockerignore`

The next work should focus on making the app reliable for daily use, not just one-off runs.

## Product Direction

The strongest direction is a personal AI intelligence dashboard:

- fewer low-value items
- visible scoring and source confidence
- history search and recall
- daily incremental updates
- personal feedback such as favorites, ignored items, and read state

The app should feel less like a generic RSS reader and more like a daily briefing system that learns what is worth keeping.

## Recommended Product Views

### 1. Today Brief

Default view for high-priority, high-score, unread content.

Useful fields:

- title
- summary
- source
- recommendation score
- published time
- whether it is new
- original link

### 2. History Search

A dedicated history view for finding previous results.

Filters to add:

- keyword
- source
- date range
- score range
- model
- favorite/read/ignored status

### 3. Topic Radar

A grouped view that clusters similar items by topic.

Example questions it should answer:

- What changed today in AI agents?
- Which open-source projects are repeatedly appearing?
- Which topics are gaining momentum over the last few days?

## Highest-Priority Engineering Work

### 1. Replace JSON History With SQLite

Current history is stored in `data/history.json`. This is fine for a prototype, but it will become hard to query and maintain.

Recommended tables:

- `runs`
  - run id
  - started/finished time
  - source count
  - fetched count
  - summarized count
  - error count

- `sources`
  - source id
  - name
  - type
  - URL
  - priority
  - pre-summarized flag

- `articles`
  - article id
  - canonical URL
  - title
  - content hash
  - source id
  - score
  - published time
  - first seen time
  - last seen time

- `summaries`
  - summary id
  - article id
  - summary text
  - model
  - token usage
  - created time

- `article_state`
  - article id
  - read flag
  - favorite flag
  - ignored flag
  - user notes

Why this matters:

- enables real history search
- prevents duplicate LLM calls
- supports incremental fetching
- unlocks statistics and trend views

### 2. Add Incremental Fetching

The app should avoid reprocessing content it has already seen.

Recommended behavior:

- fetch sources
- normalize URL/title/content
- compute stable article key
- skip already-seen items unless the content changed
- reuse existing summaries
- highlight new items

Recommended dedupe keys:

1. canonical URL
2. normalized URL without tracking params
3. content hash
4. normalized title as fallback

### 3. Add Card Actions

Each result card should support:

- favorite
- mark as read
- ignore
- open original
- copy summary
- search similar items

These actions turn the app from a passive feed into a personal workflow.

### 4. Add Score and Priority UI

AIHot already carries useful curation signal. Make that visible.

Recommended UI details:

- score badge
- source priority badge
- pre-summarized badge
- token usage badge
- new/read indicator

### 5. Move Long Runs Into Background Jobs

The current web flow runs fetch and summarize inside one request. This is okay locally, but not ideal for deployment.

Recommended flow:

1. `POST /api/jobs`
2. return job id
3. run fetch/summarize in background
4. frontend polls `GET /api/jobs/{id}`
5. frontend loads result when complete

This avoids request timeouts and supports progress display.

## Deployment Roadmap

### Phase 1: Safe GitHub Release

Already mostly prepared.

Required checks before pushing:

- `.env` is ignored
- `.venv/` is ignored
- `.uv-cache/` is ignored
- `data/history.json` is ignored
- `results.html` is ignored
- no real API keys appear in committed files
- README explains setup and run commands
- CI is present

Recommended commands:

```powershell
git status --short
git add .
git commit -m "Prepare project for GitHub deployment"
git remote add origin <repo-url>
git push -u origin main
```

### Phase 2: Self-Hosted Deployment

Use Docker first because it is portable.

Recommended features:

- Dockerfile
- `.dockerignore`
- mounted `/app/data`
- environment variables through `.env` or platform secrets

Example:

```powershell
docker build -t ai-news-summarizer .
docker run --rm -p 8000:8000 --env-file .env -v ${PWD}/data:/app/data ai-news-summarizer
```

### Phase 3: Public Web Deployment

Before exposing this to the public internet, add access protection.

Minimum viable protection:

- `ADMIN_PASSWORD`
- login page or simple HTTP basic auth
- session cookie

Why:

- the app can spend LLM API credits
- sources and history may be personal
- public endpoints could be abused

### Phase 4: Daily Automation

Add scheduled runs.

Options:

- APScheduler inside the app
- system cron on a VPS
- GitHub Actions for scheduled fetches
- deployment-platform cron

Recommended first version:

- run once every morning
- save history
- send a short summary notification

### Phase 5: Notifications

Start with webhook support, then add provider-specific integrations.

Recommended order:

1. generic webhook
2. email
3. Telegram
4. Feishu / DingTalk / WeCom
5. ntfy

## GitHub and CI Notes

Current CI should check:

- dependency installation
- source compilation
- tests
- ruff linting

Suggested future CI additions:

- Docker image build
- secret scanning
- mypy once typing issues are cleaned up
- basic API smoke test

## Security Checklist

Before public deployment:

- no real `.env` committed
- API keys only in secrets/environment variables
- history cache excluded from Git
- access control enabled
- request rate limiting added
- logs do not print API keys
- Docker image does not bake secrets

## Suggested Task Order

If only one person is moving this forward, use this order:

1. Clean remaining web template encoding issues.
2. Add SQLite persistence.
3. Implement incremental fetch and dedupe.
4. Show score/priority/new/read badges in the UI.
5. Add favorite/read/ignore actions.
6. Add a full history search page.
7. Add background jobs for long runs.
8. Add simple login protection.
9. Add scheduled daily runs.
10. Add notifications.

## Best Next Step

The most valuable next step is SQLite persistence plus incremental fetching.

Reason:

- it reduces repeated network and LLM cost
- it makes history search reliable
- it creates a foundation for favorites, read state, topic radar, and daily automation

Once that is in place, the project can become a real daily-use intelligence system instead of a one-shot summarizer.
