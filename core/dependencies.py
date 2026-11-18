# Level 2: dependency providers. Routes declare what they need, e.g.
#     service: IngestionService = Depends(get_ingestion_service)
# and FastAPI builds the chain for each request:
#     get_db -> get_document_repository -> get_ingestion_service
# Within one request every provider runs once and its result is shared, so all
# services in that request use the same database session.
# In tests (Level 4) any link can be swapped with app.dependency_overrides,
# e.g. a fake repository or a SQLite session, without touching routes or services.
#
# POST /extract path, step 4 of 10: FastAPI runs get_ingestion_service, which
# needs get_document_repository, which needs get_db (step 5, core/database.py).
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from repositories import DocumentRepository
from services import DocumentService, IngestionService


def get_document_repository(
    db: AsyncSession = Depends(get_db),           # FastAPI first opens a DB session
) -> DocumentRepository:
    return DocumentRepository(db)                 # repository that uses that session


def get_document_service(
    repository: DocumentRepository = Depends(get_document_repository),
) -> DocumentService:
    return DocumentService(repository)            # (GET /documents path, not this one)


def get_ingestion_service(
    repository: DocumentRepository = Depends(get_document_repository),  # needs the repository first
) -> IngestionService:
    return IngestionService(repository)           # handed to the route as `service`
