# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DataLine is a multi-source heterogeneous data collection platform (多源异类数据采集汇聚系统) supporting five source types: Website, API, File, Stream, External. It uses Domain-Driven Design to separate the "what to collect" (Source domain) from the "how to collect" (Crawler domain).

## Commands

### Backend (Python)

```bash
# Install all dependencies (run from ingestor/)
uv sync --all-packages

# Run development server (FastAPI with hot reload)
cd ingestor
uv run fastapi dev server/src/server/main.py

# Run all tests
cd ingestor/crawler
uv sync --group dev
uv run pytest

# Run a single test file
uv run pytest tests/core/test_link_extractor.py

# Run a single test by name
uv run pytest tests/core/test_link_extractor.py::test_function_name -v
```

### Frontend (Next.js)

```bash
# Install dependencies
cd admin && pnpm install

# Run dev server
pnpm dev

# Build for production
pnpm build

# Lint
pnpm lint
```

### Docker Deployment

```bash
# Deploy everything
./scripts/deploy-all.sh

# Deploy backend only (PostgreSQL + FastAPI)
./scripts/deploy-ingestor.sh

# Deploy frontend only
./scripts/deploy-admin.sh
```

Copy `.env.example` to `.env` before deploying. Key variables: `SERVER_PORT` (default 8000), `ADMIN_PORT` (default 3000), `DATALINE_DATABASE_URL`.

FastAPI auto-docs available at `http://localhost:8000/docs`.

## Architecture

### Repository Structure

```
dataline/
├── admin/               # Next.js 16 + React 19 + TypeScript frontend
├── ingestor/            # Python uv workspace
│   ├── crawler/         # Extraction library (installable package + CLI)
│   └── server/          # FastAPI orchestration server (depends on crawler)
└── scripts/             # Docker deployment scripts
```

### Backend: Two-Package Python Workspace

**`ingestor/crawler`** — Pure extraction library with no server dependencies:
- `crawler/source/` — Source domain: `Source`, `Line`, `SourceType`, type-based presets
- `crawler/crawler/` — Crawler domain: execution engine, extractors, downloaders, density detector

**`ingestor/server`** — FastAPI server that imports crawler as a library:
- `server/api/` — REST endpoints for sources, tasks, logs
- `server/models/` — SQLModel ORM tables (Source, Task, Log, Data)
- `server/services/crawler_service.py` — Orchestrates crawler execution
- `server/core/config.py` — Settings via `DATALINE_*` env vars

### Domain Model

```
Source (data source configuration)
  └─ Line (collection channel; one source can have many lines)
      └─ Data (individual collected items)

Crawler (execution container; manages deduplication, rate limiting)
  └─ Task (maps 1:1 to a Line)
      └─ Extractor pipeline:
          LinkExtractor → discovers URLs → DataExtractor → structured Data
```

A Source gets a default Line auto-created if none are specified (uses `Source.url`).

### Extraction Pipeline

```
List Page URL → LinkExtractor (CSS selector) → Detail URLs
                                                   ↓
                                          DataExtractor (title/time/content selectors)
                                                   ↓
                                               Data[]
```

Extractor config lives in `Line.meta["extractor_config"]`. `DensityBasedDetector` (`crawler/crawler/density.py`) can infer selectors automatically from HTML structure when they're not provided.

### Configuration Precedence (highest wins)

1. Runtime overrides
2. Crawler build options parameter
3. `Source.meta["crawler_build_options"]`
4. Type preset from `crawler/source/presets.py`

### Frontend Architecture

- API proxy: Next.js rewrites `/api/*` to `BACKEND_URL` (set at build time via Docker ARG)
- All REST calls centralized in `admin/src/lib/api.ts`
- Pages in `admin/src/app/`: dashboard, sources (CRUD), results, logs
- UI components: shadcn/ui in `src/components/ui/`, layout in `src/components/layout/`

### Testing Approach

Tests in `ingestor/crawler/tests/` use `StubDownloader` / `MappedStubDownloader` (in `tests/stubs.py`) to avoid network calls. Tests are organized by source type (`core/`, `website/`, `api/`, etc.). All tests are async-by-default (`asyncio_mode = "auto"`).

## Key Files

| File | Purpose |
|------|---------|
| `ingestor/crawler/src/crawler/__init__.py` | Public API of the crawler library |
| `ingestor/crawler/src/crawler/crawler/density.py` | Auto selector detection algorithm |
| `ingestor/crawler/src/crawler/source/presets.py` | Per-SourceType default configurations |
| `ingestor/server/src/server/core/config.py` | All server settings (env var prefix: `DATALINE_`) |
| `admin/src/lib/api.ts` | All frontend API calls |
| `admin/next.config.ts` | API proxy rewrite rules |
