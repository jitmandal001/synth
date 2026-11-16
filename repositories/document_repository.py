import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import Document, Extraction, ReviewStatus, Source


class DocumentRepository:
    """All database reads and writes for sources, documents and extractions."""

    def __init__(self, session: AsyncSession):
        # One repository per request, sharing that request's session (from get_db).
        self.session = session

    # ---------- reads ----------

    async def list_documents(self, category: str | None = None) -> list[Document]:
        """Newest first, with extractions loaded. Optionally filter by arXiv category."""
        query = (
            select(Document)
            # Load extractions in the same round trip: async SQLAlchemy can't
            # lazy-load document.extractions later, when the schema reads it.
            .options(selectinload(Document.extractions))
            .order_by(Document.id.desc())
        )
        if category:
            query = query.where(Document.category == category)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_document(self, document_id: int) -> Document | None:
        """One document with its extractions, or None if the id doesn't exist."""
        query = (
            select(Document)
            .options(selectinload(Document.extractions))
            .where(Document.id == document_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def find_latest_extraction(
        self, source_type: str, source_identifier: str
    ) -> Extraction | None:
        """Newest extraction for a source (e.g. arXiv ID), or None if never ingested.

        Level 1 fix (moved here in Level 2): used to skip re-fetching and re-running
        the LLM for a paper we already have.
        """
        query = (
            select(Extraction)
            .join(Document)                  # extraction -> its document
            .join(Source)                    # document -> its source (has the ID)
            .where(
                Source.source_type == source_type,
                Source.source_identifier == source_identifier,
            )
            .order_by(Extraction.id.desc())  # newest first
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    # ---------- writes ----------

    async def save_extraction(
        self,
        *,
        source_type: str,
        source_identifier: str,
        abstract: str,
        title: str | None,
        category: str | None,
        summary: str,
        key_entities: list[str],
        token_count: int | None,
        latency: float | None,
    ) -> Extraction:
        """Save Source -> Document -> Extraction as one transaction (all or nothing)."""
        try:
            source = Source(
                source_type=source_type,
                source_identifier=source_identifier,
                user_id=None,
            )
            self.session.add(source)
            await self.session.flush()  # sends the INSERT so source.id is known

            document = Document(
                source_id=source.id,
                abstract=abstract,
                # Level 1 fix: save metadata so /documents?category= works.
                title=title,
                category=category,
            )
            self.session.add(document)
            await self.session.flush()  # document.id is now known

            extraction = Extraction(
                document_id=document.id,
                summary=summary,
                # Storage detail kept inside the repository: Postgres column is
                # Text, so the list is stored as JSON text.
                key_entities=json.dumps(key_entities),
                token_count=token_count,
                latency=latency,
                review_status=ReviewStatus.PENDING,
            )
            self.session.add(extraction)

            await self.session.commit()  # all three rows saved together
            return extraction

        except Exception:
            await self.session.rollback()  # none of the three rows are kept
            raise
