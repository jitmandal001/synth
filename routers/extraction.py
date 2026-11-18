# POST /extract path, step 2 of 10: FastAPI matches the URL to this route.
# Before the function runs, FastAPI validates the body (step 3, schemas/extraction.py)
# and builds the service (steps 4-5, core/dependencies.py + core/database.py).
from fastapi import APIRouter, Depends

from core.dependencies import get_ingestion_service
from schemas import ResearchExtraction, ResearchRequest
from services import IngestionService

router = APIRouter(tags=["extraction"])           # mini-app holding this route; main.py plugs it in


@router.post("/extract", response_model=ResearchExtraction)  # POST /extract; reply must match ResearchExtraction
async def extract(
    request: ResearchRequest,                     # JSON body, already validated (else 422)
    service: IngestionService = Depends(get_ingestion_service),  # ready-made service, built per request
):
    """Summarize an abstract or an arXiv paper with the LLM and store the result."""
    return await service.extract(                 # hand the work to the service (step 6), wait for it
        abstract=request.abstract,                # pasted text, or None
        arxiv_id=request.arxiv_id,                # arXiv ID, or None
    )                                             # result → JSON response; errors → step 10
