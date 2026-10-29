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

PostgreSQL, authentication, persistent storage, automated tests, and production deployment are planned for later stages.

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
├── .gitignore
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
- `.gitignore` — excludes local environments, secrets, and generated files from Git.

## Setup

### 1. Create and activate a virtual environment

**macOS — PowerShell:**

```powershell
python -m venv .venv
./.venv/bin/Activate.ps1
```

**Windows — PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

`requirements.txt` lists only the packages Synth imports directly. When adding a dependency, add its pinned line by hand instead of running `pip freeze`, which records platform-specific packages (such as `uvloop`, which does not install on Windows).

### 3. Configure OpenRouter

Create an API key through [OpenRouter](https://openrouter.ai/keys).

Create a file named `.env` in the project root containing:

```text
OPENROUTER_API_KEY=YOUR_OPENROUTER_API_KEY
```

`.env` is gitignored. Keep your key private. Do not hardcode it in Python files or commit it to GitHub.

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
| 0 | FastAPI baseline, arXiv retrieval, and LLM extraction | Complete |
| 1 | PostgreSQL, SQLAlchemy, Alembic, persistent state | Planned |
| 2 | Modular FastAPI architecture and configuration | Planned |
| 3 | Authentication and role-based access control | Planned |
| 4 | Automated testing, logging, and CI | Planned |
| 5 | Docker and containerized deployment | Planned |
| 6+ | Background jobs, ETL, ML workflows, RAG, and production deployment | Planned |

## Development Workflow

Start the application from the project root:

```powershell
python -m uvicorn main:app --reload --env-file .env
```

After making changes, test the relevant endpoints through `/docs`.

Commit working changes using descriptive messages:

```powershell
git add main.py services/ requirements.txt README.md
git commit -m "Update Synth baseline documentation"
git push
```

Do not commit `.venv/`, API keys, or other secrets.

---

**Synth is being developed incrementally.** Level 0 is complete; the next step is Level 1, persistent storage with PostgreSQL.
