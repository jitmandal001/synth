# POST /extract path, step 6 of 10: the business logic ("the recipe").
# Uses the repository (step 7) for the database and the clients (steps 8-9)
# for arXiv and the LLM. Any error raised here goes to step 10.
import asyncio
from uuid import uuid4

from clients import extract_research, fetch_arxiv_paper
from core.exceptions import InvalidExtractionRequestError
from repositories import DocumentRepository
from schemas import ExtractionResponse, ResearchExtraction


class IngestionService:
    """The /extract use case: get an abstract, run the LLM on it, save the result."""

    def __init__(self, repository: DocumentRepository):
        self.repository = repository              # given by core/dependencies.py

    async def extract(
        self, *, abstract: str | None = None, arxiv_id: str | None = None
    ) -> ResearchExtraction:
        # Business rule: exactly one input must be provided.
        if (abstract is None) == (arxiv_id is None):          # both set, or both missing
            raise InvalidExtractionRequestError(              # → 400 in step 10
                "Provide exactly one of 'abstract' or 'arxiv_id'."
            )

        # Step 1: Obtain the abstract (and metadata, for arXiv papers).
        if abstract is not None:                              # user pasted text
            # Level 1 fix: pasted text has no metadata, so leave these empty.
            title = None
            category = None
            source_type = "manual"
            source_identifier = f"manual:{uuid4()}"           # unique id, so never a duplicate
        else:                                                 # user sent an arXiv ID
            # Level 1 fix: don't re-fetch, re-run the LLM or re-save a paper we
            # already have. Return the stored result instead.
            previous = await self.repository.find_latest_extraction("arxiv", arxiv_id)  # SELECT (step 7)
            if previous is not None:                          # already saved before
                # Reuse the response schema's parsing of the stored JSON entities.
                stored = ExtractionResponse.model_validate(previous)  # DB row → clean object
                return ResearchExtraction(                    # answer instantly, skip the rest
                    summary=stored.summary,
                    key_entities=stored.key_entities,
                )

            # Level 1 fix: run blocking calls in a thread so the server isn't frozen.
            paper = await asyncio.to_thread(fetch_arxiv_paper, arxiv_id)  # arXiv API (step 8)
            abstract = paper.abstract
            title = paper.title
            category = paper.category
            source_type = "arxiv"
            source_identifier = arxiv_id

        # Step 2: Generate the LLM extraction.
        result, token_count, latency = await asyncio.to_thread(extract_research, abstract)  # LLM (step 9)

        # Step 3: Save source, document and extraction in one transaction.
        await self.repository.save_extraction(                # INSERT ×3 + COMMIT (step 7)
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

        return result                                         # back to the route → JSON
