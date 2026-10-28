
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from services.arxiv import fetch_arxiv_abstract
from services.extraction import (
    ResearchExtraction,
    extract_research as run_extraction,
)

app = FastAPI(
    title="Synth API",
    description="A research intelligence backend",
    version="0.1.0",
)


class ResearchRequest(BaseModel):
    abstract: str | None = Field(
        default=None,
        min_length=1,
        description="Paste a research paper abstract",
    )
    arxiv_id: str | None = Field(
        default=None,
        description="arXiv paper ID, e.g. 1706.03762",
    )


@app.get("/")
def home():
    return {"message": "Welcome to Synth"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/extract", response_model=ResearchExtraction)
def extract_endpoint(request: ResearchRequest):
    # Exactly one input must be provided.
    if (request.abstract is None) == (request.arxiv_id is None):
        raise HTTPException(
            status_code=400,
            detail="Provide exactly one of 'abstract' or 'arxiv_id'.",
        )

    if request.abstract is not None:
        abstract = request.abstract
    else:
        abstract = fetch_arxiv_abstract(request.arxiv_id)

    return run_extraction(abstract)
