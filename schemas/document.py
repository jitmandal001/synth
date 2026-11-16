from datetime import datetime

from pydantic import BaseModel, ConfigDict

from schemas.extraction import ExtractionResponse


class DocumentResponse(BaseModel):
    """Body of GET /documents/{id}, and each item of GET /documents."""

    # Level 2: read directly from a SQLAlchemy Document. The nested
    # document.extractions list is converted with ExtractionResponse automatically.
    # The relationship must already be loaded (selectinload), because async
    # SQLAlchemy can't lazy-load it here.
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_id: int
    title: str | None
    abstract: str
    category: str | None
    created_at: datetime
    extractions: list[ExtractionResponse]
