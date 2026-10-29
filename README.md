# Synth — Research Intelligence API

Synth is a research intelligence backend that uses an LLM to extract structured information from scientific research abstracts. It currently supports manually provided abstracts and fetching abstracts from arXiv.

## Current Progress

**Level 0 — Baseline: Complete** (tagged `v0.0-baseline`)

- [x] FastAPI application setup
- [x] Health-check and home endpoints
- [x] Research abstract input validation
- [x] LLM-based summary and key entity extraction using OpenRouter
- [x] Fetching research abstracts from the arXiv API
- [x] Structured JSON responses validated with Pydantic
- [x] Retry when the free model returns empty or non-JSON output
- [x] End-to-end testing of both input paths
- [x] Level 0 GitHub milestone, pull request, and release tag

**Level 1 — PostgreSQL: In progress** (milestone *Level 01 — PostgreSQL*, issue [#7](https://github.com/jitmandal001/synth/issues/7))

Synth does not store anything yet: every paper and extraction is discarded once the response is sent. Level 1 adds a database so they survive restarts and later levels can build on them.

- [ ] Install PostgreSQL and create the `synth` database
- [ ] Async database connection with SQLAlchemy 2.0
- [ ] Tables: `users` (stub), `sources`, `documents`, `extractions`
- [ ] Alembic migrations
- [ ] Store arXiv metadata (title, category, authors) with each document
- [ ] Save every extraction with the model used, token counts, and latency
- [ ] `GET /documents?category=...` and `GET /documents/{id}`
- [ ] Add `review_status` to `extractions` in three migrations (nullable → backfill → NOT NULL)

Exit condition: the app survives a restart with zero data loss, and `alembic upgrade head` and `alembic downgrade -1` both run cleanly on a fresh database.

Authentication, automated tests, and production deployment are planned for later levels.

## Technology Stack

- **Python** — application language
- **FastAPI** — REST API framework
- **Pydantic** — request and response validation
- **OpenRouter** — access to eligible hosted LLMs
- **OpenAI Python SDK** — OpenRouter-compatible API client
- **arXiv API** — research paper metadata and abstract retrieval
- **Uvicorn** — ASGI development server

## Project Structure

```text
synth/
├── main.py
├── requirements.txt
├── .env.example
├── .gitignore
├── first-merge.html
├── README.md
└── services/
    ├── __init__.py
    ├── arxiv.py
    └── extraction.py
```

### File Responsibilities

- `main.py` — defines the FastAPI application, endpoints, and request validation.
- `services/arxiv.py` — fetches and parses abstracts from arXiv.
- `services/extraction.py` — calls OpenRouter and validates the generated summary and key entities.
- `requirements.txt` — records Python dependencies.
- `.env.example` — template listing the environment variables Synth needs; copy it to `.env`.
- `.gitignore` — excludes local environments, secrets, and generated files from Git.
- `first-merge.html` — a click-through walkthrough of the Git and GitHub workflow used in this repository (issue → branch → commit → push → pull request → merge → pull). Open it in a browser; GitHub displays `.html` files as source code.

Two folders and files exist only on your machine and are never committed: `.venv/` (the virtual environment) and `.env` (your API key).

## Setup

### 1. Create and activate a virtual environment

**Windows — PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell refuses to run `Activate.ps1`, allow local scripts once and try again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

**macOS / Linux — bash or zsh:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

`requirements.txt` lists only the packages Synth imports directly. When adding a dependency, add its pinned line by hand instead of running `pip freeze`, which records platform-specific packages (such as `uvloop`, which does not install on Windows).

### 3. Configure OpenRouter

Create an API key through [OpenRouter](https://openrouter.ai/keys).

Copy the template to create your own `.env` file:

```powershell
Copy-Item .env.example .env
```

On macOS or Linux, use `cp .env.example .env`.

Open `.env` and replace the placeholder value of `OPENROUTER_API_KEY` with your key.

`.env` is gitignored. Keep your key private. Do not hardcode it in Python files, put it in `.env.example`, or commit it to GitHub.

The application currently uses OpenRouter's `openrouter/free` model router. Eligible free models may be subject to availability and rate limits.

### 4. Run the application

From the project root:

```powershell
python -m uvicorn main:app --reload --env-file .env
```

The API will be available at:

- Home: http://127.0.0.1:8000/
- Health check: http://127.0.0.1:8000/health
- Interactive API documentation: http://127.0.0.1:8000/docs

## API Endpoints

### `GET /`

Returns a welcome message.

Example response:

```json
{
  "message": "Welcome to Synth"
}
```

### `GET /health`

Returns a basic application health response.

Example response:

```json
{
  "status": "healthy"
}
```

This endpoint confirms that the application responds; it does not verify external LLM availability.

### `POST /extract`

Extracts a summary and key entities from a research abstract.

The request must contain **exactly one** of the following fields:

- `abstract` — a manually supplied research abstract.
- `arxiv_id` — an arXiv paper identifier used to fetch the abstract automatically.

#### Option A: Provide an abstract

Request:

```json
{
  "abstract": "We propose a transformer-based model for classifying scientific documents."
}
```

#### Option B: Provide an arXiv ID

Request:

```json
{
  "arxiv_id": "1706.03762"
}
```

Synth fetches the paper's abstract from arXiv and passes it to the LLM.

#### Response format

The endpoint returns a JSON object containing:

```json
{
  "summary": "A concise summary generated from the research abstract.",
  "key_entities": [
    "transformer-based model",
    "scientific document classification"
  ]
}
```

The example values are illustrative; actual output depends on the abstract and selected model.

## Error Handling

The API validates incoming requests and may return errors when:

- Neither input field is supplied, or both are supplied.
- The arXiv ID is malformed (`400`) or matches no paper (`404`).
- arXiv cannot be reached (`502`).
- The OpenRouter API key is missing or invalid.
- The selected free model is unavailable or rate-limited.
- The LLM response is empty or does not match the expected schema on all three attempts. `openrouter/free` may route each attempt to a different free model.

## Current Limitations

- Extracted results are not persisted.
- No database is configured.
- No authentication or authorization is implemented.
- LLM output quality has not yet been systematically evaluated.
- Free hosted model availability and latency can vary.
- Automated test coverage and CI are not yet implemented.

## Roadmap

| Level | Focus | Status |
|---|---|---|
| 0 | FastAPI baseline, arXiv retrieval, and LLM extraction | Complete (`v0.0-baseline`) |
| 1 | PostgreSQL, SQLAlchemy, Alembic, persistent state | In progress ([#7](https://github.com/jitmandal001/synth/issues/7)) |
| 2 | Modular FastAPI architecture and configuration | Planned |
| 3 | Authentication and role-based access control | Planned |
| 4 | Automated testing, logging, and CI | Planned |
| 5 | Docker and containerized deployment | Planned |
| 6+ | Background jobs, ETL, ML workflows, RAG, and production deployment | Planned |

## Development Workflow

Every change goes through an issue, a branch, and a pull request, so `main` always holds working code.

1. **Open an issue** describing the change. Roadmap levels go under that level's milestone; small standalone fixes get a label such as `documentation` or `bug` instead.

2. **Start a branch from an up-to-date `main`:**

   ```powershell
   git checkout main
   git pull
   git checkout -b level-1-postgres
   ```

3. **Make small commits**, one per sub-step:

   ```powershell
   git add <files>
   git commit -m "Add async database session"
   ```

4. **Push the branch:**

   ```powershell
   git push -u origin level-1-postgres
   ```

5. **Open a pull request** into `main` on GitHub. Put `Closes #<issue number>` in the description, and say what changed and how it was tested.

6. **Merge** with *Create a merge commit*, then bring your local `main` up to date:

   ```powershell
   git checkout main
   git pull
   ```

7. **At the end of each level**, tag the merge commit and push the tag:

   ```powershell
   git tag -a v0.1-postgres -m "Level 1: PostgreSQL"
   git push origin v0.1-postgres
   ```

Before opening a pull request, run the app and test the relevant endpoints through `/docs`. Never commit `.venv/`, `.env`, API keys, or other secrets.

---

**Synth is being developed incrementally.** Level 0 is complete (`v0.0-baseline`); Level 1, persistent storage with PostgreSQL, is in progress.
