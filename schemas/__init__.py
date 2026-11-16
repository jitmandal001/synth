# Level 2: Pydantic schemas = the shape of data going in and out of the API.
# models/ describes database tables; schemas/ describes requests and responses.
# Keeping them apart means the API can change without touching the DB, and vice versa.
from schemas.document import DocumentResponse
from schemas.extraction import ExtractionResponse, ResearchExtraction, ResearchRequest

__all__ = [
    "DocumentResponse",
    "ExtractionResponse",
    "ResearchExtraction",
    "ResearchRequest",
]
