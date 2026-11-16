from fastapi import APIRouter, Depends

from core.dependencies import get_document_service
from schemas import DocumentResponse
from services import DocumentService

# prefix: every path below starts with /documents. tags: groups them in /docs.
router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    category: str | None = None,
    service: DocumentService = Depends(get_document_service),
):
    """Stored documents, newest first. Filter with ?category=cs.CL"""
    return await service.list_documents(category)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    service: DocumentService = Depends(get_document_service),
):
    """One document with all its extractions. 404 if the id doesn't exist."""
    return await service.get_document(document_id)
