# ProductAI — Claude Code Instructions

## Project Overview

ProductAI is an AI-powered Product Management Service. FastAPI backend with Jinja2 server-rendered pages, SQLite database, and Anthropic Claude integration for AI features.

## Commands

```bash
# Run locally
./run.sh --reload

# Run with base path (for reverse proxy)
BASE_PATH=/productai ./run.sh --port 5010

# Docker build & run
docker build -t productai .
docker run -d -p 8000:8000 -e BASE_PATH=/productai productai

# Lock dependencies
uv lock
```

## Architecture

- **Entry point**: `productai/app.py` — FastAPI with `root_path=BASE_PATH`, lifespan runs DB migrations
- **Routes**: `productai/routes/pages.py` (HTML pages), `productai/routes/api.py` (API + AI streaming)
- **AI**: `productai/ai/service.py` (Claude streaming), `productai/ai/prompts.py` (system prompts), `productai/ai/autocomplete.py` (word suggestions)
- **DB**: `productai/db/schema.py` (init + migrations), `productai/db/models.py` (async CRUD)
- **Migrations**: `productai/db/migrations/` — numbered SQL files, applied in order on startup
- **Templates**: `productai/templates/base.html` (layout + sidebar + JS utils), pages in `productai/templates/pages/`

## Key Patterns

### BASE_PATH
All URLs must be prefixed with `BASE_PATH` for reverse proxy support:
- Python: `BASE_PATH = os.environ.get("BASE_PATH", "").rstrip("/")`
- Templates: `{{ base_path }}` Jinja2 global for hrefs
- JS: `BASE_PATH` variable (set in base.html after content block) — use `'{{ base_path }}'` in page-level scripts
- API redirects: `f"{BASE_PATH}/path"`

### Database
- SQLite with WAL mode and foreign keys enabled
- All DB access through `productai/db/models.py` async functions
- Migrations auto-apply on startup (tracked in `_migrations` table)
- Entity types: `project`, `plan`, `prd` — hierarchical (project > plan > prd), relationships optional

### AI Streaming
- SSE pattern: `StreamingResponse` with `text/event-stream`
- Client-side: `streamAI()` utility in base.html handles SSE parsing
- AI sessions stored per entity in `ai_sessions` table

### Templates
- All pages extend `base.html`
- Sidebar is collapsible (state in localStorage)
- Markdown rendered client-side with `marked.js`
- Autocomplete uses debounced fetch to `/api/autocomplete/words`

## Deployment

Target: `adrian@devstar2.local` via Docker
- Build dir: `~/productai-build/`
- DB volume: `~/productai-data/productai.db:/app/productai.db`
- Port: `127.0.0.1:5010->8000`
- Nginx route: managed via `~/personal/local_proxy/manage.sh`

## Style

- Use async/await for all DB and AI operations
- Keep templates using Tailwind utility classes
- PRD/Plan forms use the `enhance-field-row` pattern for AI enhancement buttons
- Follow existing migration numbering (next: 007)
