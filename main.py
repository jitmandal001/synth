import asyncio
import json
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db  # Level 2: was "from db import get_db"
from models import Source, Document, Extraction, ReviewStatus
# Level 2: request/response shapes now live in schemas/ instead of this file.
from schemas import DocumentResponse, ResearchExtraction, ResearchRequest

from services.arxiv import fetch_arxiv_paper  # Level 1 fix: returns title/category too
from services.extraction import extract_research as run_extraction


app = FastAPI(
    title="Synth API",
    description="A research intelligence backend",
    version="0.1.0",
)


@app.get("/documents", response_model=list[DocumentResponse])
async def get_documents(
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Document)
        .options(selectinload(Document.extractions))
        .order_by(Document.id.desc())
    )

    if category:
        query = query.where(Document.category == category)

    result = await db.execute(query)
    documents = result.scalars().all()

    # Level 2: from_attributes in DocumentResponse replaces format_document().
    return [DocumentResponse.model_validate(document) for document in documents]


@app.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Document)
        .options(selectinload(Document.extractions))
        .where(Document.id == document_id)
    )

    result = await db.execute(query)
    document = result.scalar_one_or_none()

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
        existing = await db.execute(
            select(Extraction)
            .join(Document)                 # extraction -> its document
            .join(Source)                   # document -> its source (has the arXiv ID)
            .where(
                Source.source_type == "arxiv",
                Source.source_identifier == request.arxiv_id,
            )
            .order_by(Extraction.id.desc())  # newest extraction first
            .limit(1)
        )
        previous = existing.scalar_one_or_none()

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

    try:
        # Step 3: Create the source record.
        source = Source(
            source_type=source_type,
            source_identifier=source_identifier,
            user_id=None,
        )

        db.add(source)
        await db.flush()

        # Step 4: Create the document record.
        document = Document(
            source_id=source.id,
            abstract=abstract,
            # Level 1 fix: save metadata so /documents?category= works.
            title=title,
            category=category,
        )

        db.add(document)
        await db.flush()

        # Step 5: Create the extraction record.
        extraction = Extraction(
            document_id=document.id,
            summary=result.summary,
            key_entities=json.dumps(result.key_entities),
            token_count=token_count,
            latency=latency,
            review_status=ReviewStatus.PENDING,
        )

        db.add(extraction)

        # Step 6: Save all three records.
        await db.commit()

    except Exception:
        await db.rollback()
        raise

    # Step 7: Return the original API response.
    return result
