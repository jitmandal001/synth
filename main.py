import asyncio
import json
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db  # Level 2: was "from db import get_db"
# Level 2: all database queries live in the repository; this file has no SQL.
from repositories import DocumentRepository
# Level 2: request/response shapes now live in schemas/ instead of this file.
from schemas import DocumentResponse, ResearchExtraction, ResearchRequest

# Level 2: outside-API code moved from services/ to clients/.
from clients import fetch_arxiv_paper  # Level 1 fix: returns title/category too
from clients import extract_research as run_extraction
from core.exceptions import (
    ArxivPaperNotFoundError,
    ArxivUnavailableError,
    InvalidArxivIdError,
    LLMExtractionError,
    LLMNotConfiguredError,
    SynthError,
)


app = FastAPI(
    title="Synth API",
    description="A research intelligence backend",
    version="0.1.0",
)


# Level 2: the ONE place that decides which HTTP status each app error gets.
# Clients/services raise plain Python errors; this turns them into responses
# with the same codes and {"detail": "..."} body HTTPException used to produce.
ERROR_STATUS_CODES: dict[type[SynthError], int] = {
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


@app.get("/documents", response_model=list[DocumentResponse])
async def get_documents(
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    documents = await DocumentRepository(db).list_documents(category)

    # Level 2: from_attributes in DocumentResponse replaces format_document().
    return [DocumentResponse.model_validate(document) for document in documents]


@app.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
):
    document = await DocumentRepository(db).get_document(document_id)

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    return DocumentResponse.model_validate(document)

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
    repo = DocumentRepository(db)  # Level 2: every DB call below goes through this

    # Exactly one input must be provided.
    if (request.abstract is None) == (request.arxiv_id is None):
        raise HTTPException(
            status_code=400,
            detail="Provide exactly one of 'abstract' or 'arxiv_id'.",
        )

    # Step 1: Obtain the abstract.
    if request.abstract is not None:
        abstract = request.abstract
        # Level 1 fix: pasted text has no metadata, so leave these empty.
        title = None
        category = None
        source_type = "manual"
        source_identifier = f"manual:{uuid4()}"
    else:
        # Level 1 fix: the same arXiv ID was being re-fetched, re-sent to the
        # LLM and saved again. Look it up first and return the stored result.
        previous = await repo.find_latest_extraction("arxiv", request.arxiv_id)

        if previous is not None:
            # Already ingested: skip arXiv, the LLM and the inserts.
            return ResearchExtraction(
                summary=previous.summary,
                key_entities=json.loads(previous.key_entities),
            )

        # Level 1 fix: keep arXiv's title/category instead of discarding them.
        # Level 1 fix: run blocking calls in a thread so the server isn't frozen.
        paper = await asyncio.to_thread(fetch_arxiv_paper, request.arxiv_id)
        abstract = paper.abstract
        title = paper.title
        category = paper.category
        source_type = "arxiv"
        source_identifier = request.arxiv_id

    # Step 2: Generate the LLM extraction.
    result, token_count, latency = await asyncio.to_thread(run_extraction, abstract)

    # Step 3: Save source, document and extraction in one transaction.
    # Level 2: the add/flush/commit/rollback code moved into the repository.
    await repo.save_extraction(
        source_type=source_type,
        source_identifier=source_identifier,
        abstract=abstract,
        title=title,
        category=category,
        summary=result.summary,
        key_entities=result.key_entities,
        token_count=token_count,
        latency=latency,
    )

    # Step 4: Return the original API response.
    return result
