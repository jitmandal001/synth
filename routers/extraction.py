from fastapi import APIRouter, Depends

from core.dependencies import get_ingestion_service
from schemas import ResearchExtraction, ResearchRequest
from services import IngestionService

router = APIRouter(tags=["extraction"])


@router.post("/extract", response_model=ResearchExtraction)
async def extract(
    request: ResearchRequest,
    service: IngestionService = Depends(get_ingestion_service),
):
    """Summarize an abstract or an arXiv paper with the LLM and store the result."""
    return await service.extract(
        abstract=request.abstract,
        arxiv_id=request.arxiv_id,
    )
