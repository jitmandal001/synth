# Level 2: main.py only builds the app and plugs the pieces together.
# Routes live in routers/, logic in services/, SQL in repositories/,
# outside APIs in clients/, settings and wiring in core/.
from fastapi import FastAPI

from core.error_handlers import register_exception_handlers
from routers import documents, extraction, health

app = FastAPI(
    title="Synth API",
    description="A research intelligence backend",
    version="0.2.0",  # Level 2: layered architecture
)

register_exception_handlers(app)

app.include_router(health.router)
app.include_router(extraction.router)
app.include_router(documents.router)
