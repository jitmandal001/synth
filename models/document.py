from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base

if TYPE_CHECKING:  # only for type checkers/IDE; avoids circular imports at runtime
    from models.extraction import Extraction
    from models.source import Source


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(
        ForeignKey("sources.id"), unique=True
    )
    title: Mapped[str | None] = mapped_column(String(500))
    abstract: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    source: Mapped["Source"] = relationship(
        back_populates="document"
    )
    extractions: Mapped[list["Extraction"]] = relationship(
        back_populates="document"
    )
