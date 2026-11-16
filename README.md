# Synth — Research Intelligence API

Synth is a research intelligence backend that uses Large Language Models (LLMs) to extract structured summaries and key entities from scientific research abstracts. It supports manually provided abstracts and automatic retrieval from arXiv.

## Current Progress

### Level 0 — Baseline <badge>Complete</badge>

- FastAPI application and API endpoints.
- LLM-based extraction using OpenRouter.
- arXiv abstract retrieval.
- Pydantic response validation and end-to-end testing.
- Release: `v0.0-baseline`.

### Level 1 — PostgreSQL Persistence <badge>Complete</badge>

- [x] PostgreSQL database integration.
- [x] Async SQLAlchemy connection using `asyncpg`.
- [x] Four database models: `users`, `sources`, `documents`, and `extractions`.
- [x] Initial Alembic schema migration.
- [x] Three migrations for `extractions.review_status` (nullable → backfill → NOT NULL).
- [x] Persistent storage of extraction results.
- [x] Extraction metrics: token count and processing latency.
- [x] Review status tracking (`pending`, `approved`, `rejected`).
- [x] Document retrieval endpoints with category filtering.
- [x] Persistence verification across application restarts.
- [x] Fresh database migration, downgrade, and re-upgrade verification.

**Level 1 fixes:**

- [x] arXiv title and primary category are saved, so `/documents?category=` returns results.
- [x] Duplicate arXiv ingestion prevented: unique constraint on `sources (source_type, source_identifier)`, and `/extract` returns the stored extraction for an already-ingested ID.
- [x] Blocking arXiv and LLM calls run in a worker thread (`asyncio.to_thread`) so the event loop stays responsive.
- [x] Release: `v0.1.1-postgres` (`v0.1-postgres` is Level 1 before these fixes).

### Level 2 — Layered FastAPI Architecture <badge>Complete</badge>

- [x] Configuration centralized in `core/config.py` (`Settings(BaseSettings)`, secrets as `SecretStr`); no `os.getenv` elsewhere.
- [x] Database engine/session in `core/database.py`; models split into a `models/` package.
- [x] Request/response shapes in `schemas/`, read straight from ORM objects (`from_attributes`).
- [x] All SQL in `repositories/document_repository.py`.
- [x] arXiv and LLM code in `clients/`; they raise app errors (`core/exceptions.py`), not `HTTPException`.
- [x] Business logic in `services/` (`IngestionService`, `DocumentService`).
- [x] Thin routes in `routers/`, with services injected through `Depends` (`core/dependencies.py`).
- [x] One error handler maps app errors to status codes (`core/error_handlers.py`).
- [x] `GET /config-check` reports the active environment without secrets.
- [x] Same behaviour before and after: smoke test 11/11 at every step.
- [x] Verified the app runs on SQLite by changing only `DATABASE_URL`.
- [x] Release: `v0.2-layered-arch`.

## Technology Stack

Python · FastAPI · Pydantic · pydantic-settings · OpenRouter · arXiv API · PostgreSQL · SQLAlchemy (async) · asyncpg · Alembic · Uvicorn

## Architecture

Each request passes through layers that each have one job:

```text
Router  ──►  Service  ──►  Repository  ──►  PostgreSQL
(HTTP)       (logic)   │   (SQL)
                       └──►  Clients  ──►  arXiv API / OpenRouter LLM
```

| Layer | Folder | Knows about | Never does |
|---|---|---|---|
| Routers | `routers/` | HTTP: paths, request bodies, `Depends` | SQL, business rules |
| Services | `services/` | the use case: which input, duplicate check, fetch, LLM, save | HTTP status codes, SQL |
| Repositories | `repositories/` | SQLAlchemy queries and transactions | business rules |
| Clients | `clients/` | outside APIs | HTTP status codes, the database |
| Schemas | `schemas/` | API request/response shapes | database access |
| Models | `models/` | database tables | API shapes |
| Core | `core/` | settings, DB session, errors, dependency wiring | — |

Errors: clients and services raise `SynthError` subclasses (`core/exceptions.py`); `core/error_handlers.py` turns them into status codes in one place.

## Project Structure

```text
synth/
├── main.py                   # creates the app, registers error handlers, includes routers
├── core/
│   ├── config.py             # Settings(BaseSettings), get_settings()
│   ├── database.py           # async engine, SessionLocal, Base, get_db
│   ├── dependencies.py       # get_db -> repository -> service providers
│   ├── exceptions.py         # SynthError and its subclasses
│   └── error_handlers.py     # SynthError -> HTTP status code
├── routers/
│   ├── health.py             # /, /health, /config-check
│   ├── extraction.py         # POST /extract
│   └── documents.py          # GET /documents, GET /documents/{id}
├── services/
│   ├── ingestion_service.py  # extract: lookup -> fetch -> LLM -> save
│   └── document_service.py   # list / get documents
├── repositories/
│   └── document_repository.py
├── clients/
│   ├── arxiv_client.py       # fetch_arxiv_paper
│   └── llm_client.py         # extract_research (OpenRouter)
├── schemas/
│   ├── extraction.py         # ResearchRequest, ResearchExtraction, ExtractionResponse
│   └── document.py           # DocumentResponse
├── models/
│   ├── user.py  source.py  document.py  extraction.py
├── alembic.ini
├── alembic/
│   ├── env.py
│   └── versions/
├── scripts/
│   ├── check_db.py           # can we reach the database?
│   └── smoke_test_for_L2.py  # checks every endpoint against a running server
├── docs/
│   └── roadmap.html
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

### 1. Create and activate a virtual environment

**Windows (PowerShell):**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure PostgreSQL

Create a PostgreSQL database named `synth`.

### 4. Configure environment variables

Copy `.env.example` to `.env` and configure:

```env
OPENROUTER_API_KEY=your_api_key
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/synth
ENVIRONMENT=dev
```

`DATABASE_URL` is required: the app won't start without it. `ENVIRONMENT` must be `dev`, `staging` or `prod`. Optional overrides (`LLM_MODEL`, `OPENROUTER_BASE_URL`, `ARXIV_API_BASE_URL`) and their defaults are in `core/config.py`. Real environment variables take priority over `.env`.

Keep `.env` private and never commit credentials. Check what the app picked up with `GET /config-check`.

### 5. Run database migrations

```bash
alembic upgrade head
```

### 6. Start the API

```bash
uvicorn main:app --reload
```

API documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Welcome message |
| GET | `/health` | Application health |
| GET | `/config-check` | Active environment and settings, without secrets |
| POST | `/extract` | Extract summary and key entities and persist results |
| GET | `/documents` | Retrieve stored documents, optionally filtered by category |
| GET | `/documents/{id}` | Retrieve a document and its associated extractions |

### Extraction Input

`POST /extract` accepts exactly one of:

- `abstract`: Manually supplied research abstract.
- `arxiv_id`: arXiv paper identifier.

Sending both or neither returns `400`. Re-submitting an `arxiv_id` that was already ingested returns the stored extraction without calling arXiv or the LLM.

### Errors

| Status | When |
|---|---|
| 400 | both/neither input, or a malformed arXiv ID |
| 404 | unknown arXiv ID, paper without abstract, or unknown document id |
| 422 | request body fails validation (e.g. empty `abstract`) |
| 500 | `OPENROUTER_API_KEY` not configured |
| 502 | arXiv or the LLM could not be reached or returned unusable output |

Every error body has the form `{"detail": "..."}`.

### Extraction Persistence

A successful extraction is stored across three related tables:

- `sources`: Records the source and its identifier.
- `documents`: Stores the research abstract and document information.
- `extractions`: Stores the generated summary, key entities, token count, latency, and review status.

### Document Retrieval

- `GET /documents?category=cs.LG` retrieves documents matching a category.
- `GET /documents/{id}` retrieves an individual document with its associated extractions.

## Roadmap

| Level | Focus | Status |
|---|---|---|
| 0 | FastAPI and LLM extraction | Complete |
| 1 | PostgreSQL and persistent storage | Complete |
| 2 | Modular FastAPI architecture | Complete |
| 3 | Authentication and authorization | Next |
| 4 | Testing, logging and CI | Planned |
| 5 | Docker and deployment | Planned |
| 6+ | Background jobs, ETL, ML workflows and RAG | Planned |

## Development

Development follows an issue → branch → commit → pull request workflow.

Releases are tagged at each level: `v0.0-baseline`, `v0.1.1-postgres`, `v0.2-layered-arch`.

- Check the database connection: `python scripts/check_db.py`
- Check every endpoint (server must be running): `python scripts/smoke_test_for_L2.py` (add `--llm` to include real extractions)
- The full roadmap is in [docs/roadmap.html](docs/roadmap.html).

The next level adds authentication and role-based access control (Level 3).

Never commit `.env`, `.venv/`, API keys, or database credentials.
