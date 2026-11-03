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

**Note:** The database schema includes document title and category fields. Automatic arXiv metadata population is a future improvement.

## Technology Stack

Python · FastAPI · Pydantic · OpenRouter · arXiv API · PostgreSQL · SQLAlchemy (async) · asyncpg · Alembic · Uvicorn

## Project Structure

```text
synth/
├── main.py
├── db.py
├── models.py
├── alembic.ini
├── alembic/
│   ├── env.py
│   └── versions/
├── services/
│   ├── __init__.py
│   ├── arxiv.py
│   └── extraction.py
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
```

Keep `.env` private and never commit credentials.

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
| POST | `/extract` | Extract summary and key entities and persist results |
| GET | `/documents` | Retrieve stored documents, optionally filtered by category |
| GET | `/documents/{id}` | Retrieve a document and its associated extractions |

### Extraction Input

`POST /extract` accepts exactly one of:

- `abstract`: Manually supplied research abstract.
- `arxiv_id`: arXiv paper identifier.

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
| 2 | Modular FastAPI architecture | Next |
| 3 | Authentication and authorization | Planned |
| 4 | Testing, logging and CI | Planned |
| 5 | Docker and deployment | Planned |
| 6+ | Background jobs, ETL, ML workflows and RAG | Planned |

## Development

Development follows an issue → branch → commit → pull request workflow.

Level 1 implementation is maintained on the `level-1-postgres` branch.

The next development phase focuses on modular FastAPI architecture, separating routers, services, schemas, database access, and configuration.

Never commit `.env`, `.venv/`, API keys, or database credentials.
