# ProductAI

AI-powered Product Management Service with Plan Mode, PRD Generation, and interactive mindmap visualization.

## Features

- **Projects** — organize work with status, priority, team members, milestones, and timelines
- **Plans** — structured product plans with vision, goals, target audience, and success metrics
- **PRDs** — product requirements documents with AI-assisted generation and refinement
- **AI Plan Mode** — conversational product strategy assistant (Claude-powered)
- **AI Enhancement** — 3-level text enhancement (light/medium/heavy) for any field
- **Mindmap** — interactive D3.js visualization of your project hierarchy (Projects > Plans > PRDs)
- **Version History** — full snapshot-based versioning for every entity change
- **Autocomplete** — full English dictionary with frequency-ranked suggestions and PM vocabulary boost
- **Analytics** — PRD complexity ranking with stacked bar charts showing per-field text size
- **Dashboard** — filterable overview with toggle visibility for Projects/Plans/PRDs and search

## Tech Stack

- **Backend**: FastAPI + Uvicorn (async Python 3.13)
- **Database**: SQLite with aiosqlite, WAL mode, auto-migrations
- **AI**: Anthropic Claude (streaming SSE)
- **Frontend**: Jinja2 templates, Tailwind CSS, HTMX, D3.js (mindmap)
- **Autocomplete**: NLTK words/Brown corpus + english-words package

## Quick Start

```bash
# Set your Anthropic API key
export ANTHROPIC_API_KEY=your-key-here

# Run with uv
./run.sh

# Or with options
./run.sh --port 5010 --reload --base-path /productai
```

The app starts at `http://localhost:8000`. The database is created automatically on first run with demo data.

## Docker

```bash
docker build -t productai .
docker run -d \
  -p 8000:8000 \
  -e ANTHROPIC_API_KEY=your-key \
  -e BASE_PATH=/productai \
  -v ./data/productai.db:/app/productai.db \
  productai
```

## Reverse Proxy

Set `BASE_PATH` environment variable (e.g. `/productai`) for deployment behind a reverse proxy. This prefixes all routes, redirects, and static asset URLs.

## Project Structure

```
productai/
  app.py              # FastAPI app entry point
  ai/
    service.py         # Claude streaming (plan chat, PRD gen, enhancement)
    prompts.py         # System prompts for each AI mode
    autocomplete.py    # Word suggestion engine
  db/
    schema.py          # DB connection, migrations
    models.py          # Data access layer (CRUD)
    migrations/        # SQL migration files (001-006)
  routes/
    pages.py           # Page routes (Jinja2 templates)
    api.py             # API routes (CRUD, AI streaming, mindmap data)
  templates/
    base.html          # Layout with collapsible sidebar
    pages/             # All page templates
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Dashboard |
| GET | `/mindmap` | Interactive mindmap |
| GET | `/analytics` | PRD complexity charts |
| GET | `/projects/{id}` | Project detail |
| GET | `/plans/{id}` | Plan detail |
| GET | `/plans/{id}/chat` | Plan AI chat |
| GET | `/prds/{id}` | PRD detail |
| GET | `/prds/{id}/chat` | PRD AI chat |
| POST | `/api/projects` | Create project |
| POST | `/api/plans` | Create plan |
| POST | `/api/prds` | Create PRD |
| POST | `/api/ai/enhance` | Stream field enhancement |
| POST | `/api/ai/plan/{id}/chat` | Stream plan conversation |
| POST | `/api/ai/prd/generate` | Stream PRD generation |
| GET | `/api/mindmap/data` | Mindmap tree JSON |
| GET | `/api/analytics/prd-complexity` | PRD complexity data |
| POST | `/api/autocomplete/words` | Word suggestions |
| GET | `/admin` | Settings page |
