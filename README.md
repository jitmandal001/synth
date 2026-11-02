# Synth — Research Intelligence API

Synth is a research intelligence backend that uses an LLM to extract structured summaries and key entities from scientific research abstracts. It supports manually provided abstracts and automatic retrieval from arXiv.

## Current Progress

### Level 0 — Baseline <badge>Complete</badge>
- FastAPI application and API endpoints.
- LLM-based extraction using OpenRouter.
- arXiv abstract retrieval.
- Pydantic response validation and end-to-end testing.
- Release: `v0.0-baseline`.

### Level 1 — PostgreSQL <badge>In progress</badge>
- [x] PostgreSQL database setup.
- [x] Async SQLAlchemy connection using `asyncpg`.
- [x] Four models: `users`, `sources`, `documents`, `extractions`.
- [x] Initial Alembic schema migration.
- [x] Three migrations for `extractions.review_status` (nullable → backfill → NOT NULL).
- [ ] Persist extraction results in PostgreSQL.
- [ ] Store arXiv metadata and extraction metrics.
- [ ] Implement document retrieval endpoints.
- [ ] Verify persistence and migration rollback.

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

1. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a PostgreSQL database named `synth_db`.

4. Copy `.env.example` to `.env` and configure:

```env
OPENROUTER_API_KEY=your_api_key
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/synth_db
```

Keep `.env` private and never commit credentials.

5. Run database migrations:

```bash
alembic upgrade head
```

6. Start the API:

```bash
python -m uvicorn main:app --reload --env-file .env
```

API documentation: `http://127.0.0.1:8000/docs`

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Welcome message |
| GET | `/health` | Application health |
| POST | `/extract` | Extract summary and key entities |

`POST /extract` accepts exactly one of:

- `abstract`: manually supplied research abstract.
- `arxiv_id`: arXiv paper identifier.

## Roadmap

| Level | Focus | Status |
|---|---|---|
| 0 | FastAPI and LLM extraction | Complete |
| 1 | PostgreSQL and persistent storage | In progress |
| 2 | Modular FastAPI architecture | Planned |
| 3 | Authentication and authorization | Planned |
| 4 | Testing, logging and CI | Planned |
| 5 | Docker and deployment | Planned |
| 6+ | Background jobs, ETL, ML workflows and RAG | Planned |

## Development

Development follows an issue → branch → commit → pull request workflow. Level 1 work is maintained on the `level-1-postgres` branch.

Never commit `.env`, `.venv/`, API keys, or database credentials.