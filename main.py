from fastapi import FastAPI, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db  # Level 2: was "from db import get_db"
from core.exceptions import (
    ArxivPaperNotFoundError,
    ArxivUnavailableError,
    DocumentNotFoundError,
    InvalidArxivIdError,
    InvalidExtractionRequestError,
    LLMExtractionError,
    LLMNotConfiguredError,
    SynthError,
)
# Level 2: all database queries live in the repository; this file has no SQL.
from repositories import DocumentRepository
# Level 2: request/response shapes now live in schemas/ instead of this file.
from schemas import DocumentResponse, ResearchExtraction, ResearchRequest
# Level 2: business logic lives in services/; routes only call them.
from services import DocumentService, IngestionService


app = FastAPI(
    title="Synth API",
    description="A research intelligence backend",
    version="0.1.0",
)


# Level 2: the ONE place that decides which HTTP status each app error gets.
# Clients/services raise plain Python errors; this turns them into responses
# with the same codes and {"detail": "..."} body HTTPException used to produce.
ERROR_STATUS_CODES: dict[type[SynthError], int] = {
    InvalidExtractionRequestError: 400,
    DocumentNotFoundError: 404,
    InvalidArxivIdError: 400,
    ArxivPaperNotFoundError: 404,
    ArxivUnavailableError: 502,
    LLMNotConfiguredError: 500,
    LLMExtractionError: 502,
}


@app.exception_handler(SynthError)
async def synth_error_handler(request: Request, exc: SynthError) -> JSONResponse:
    status_code = ERROR_STATUS_CODES.get(type(exc), 500)  # unknown SynthError -> 500
    return JSONResponse(status_code=status_code, content={"detail": str(exc)})


# Level 2: routes are thin. Each one builds its service, calls one method and
# returns the result. Step 7 moves them into routers/ and injects the services
# with Depends instead of building them here.

@app.get("/documents", response_model=list[DocumentResponse])
async def get_documents(
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await DocumentService(DocumentRepository(db)).list_documents(category)


@app.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await DocumentService(DocumentRepository(db)).get_document(document_id)


@app.get("/")
def home():
    return {"message": "Welcome to Synth"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/extract", response_model=ResearchExtraction)
async def extract_endpoint(
    request: ResearchRequest,
    db: AsyncSession = Depends(get_db),
):
    return await IngestionService(DocumentRepository(db)).extract(
        abstract=request.abstract,
        arxiv_id=request.arxiv_id,
    )
