# POST /extract path, step 3 of 10: FastAPI checks the JSON body against
# ResearchRequest before the route runs. ResearchExtraction is the reply shape.
# (ExtractionResponse is also used on this path, by the service's duplicate check.)
import json
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ResearchRequest(BaseModel):
    """Body of POST /extract. The route checks that exactly one field is set."""

    abstract: str | None = Field(                 # optional pasted abstract
        default=None,                             # missing → None
        min_length=1,                             # "" is rejected with 422
        description="Paste a research paper abstract",
    )
    arxiv_id: str | None = Field(                 # optional arXiv ID
        default=None,
        description="arXiv paper ID, e.g. 1706.03762",
    )


class ResearchExtraction(BaseModel):
    """What the LLM must return, and what POST /extract responds with."""

    summary: str                                  # one-paragraph summary
    key_entities: list[str]                       # list of names/terms


class ExtractionResponse(BaseModel):
    """One stored extraction, as shown inside GET /documents responses."""

    # Level 2: from_attributes lets Pydantic read straight from a SQLAlchemy
    # Extraction object (extraction.summary, extraction.id, ...), replacing the
    # field-by-field copying that format_document() did in main.py.
    model_config = ConfigDict(from_attributes=True)

    id: int
    summary: str
    key_entities: list[str]
    token_count: int | None
    latency: float | None
    review_status: str
    created_at: datetime

    @field_validator("key_entities", mode="before")
    @classmethod
    def parse_key_entities(cls, value):
        # The DB stores entities as JSON text ('["a", "b"]'); the API returns a list.
        return json.loads(value) if isinstance(value, str) else value

    @field_validator("review_status", mode="before")
    @classmethod
    def enum_to_value(cls, value):
        # The DB gives ReviewStatus.PENDING; the API returns "pending".
        return value.value if isinstance(value, Enum) else value
