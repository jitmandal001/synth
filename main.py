# Level 2: main.py only builds the app and plugs the pieces together.
# Routes live in routers/, logic in services/, SQL in repositories/,
# outside APIs in clients/, settings and wiring in core/.
#
# POST /extract path, step 1 of 10: the request enters here.
# Next: routers/extraction.py
from fastapi import FastAPI

from core.error_handlers import register_exception_handlers
from routers import documents, extraction, health

app = FastAPI(                                    # the web application object uvicorn runs
    title="Synth API",                            # name shown on /docs
    description="A research intelligence backend",
    version="0.2.0",  # Level 2: layered architecture
)

register_exception_handlers(app)                  # any SynthError → JSON error with the right status

app.include_router(health.router)                 # adds GET /, /health, /config-check
app.include_router(extraction.router)             # adds POST /extract  ← this path
app.include_router(documents.router)              # adds GET /documents, /documents/{id}
