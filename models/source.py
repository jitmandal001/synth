from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base

if TYPE_CHECKING:  # only for type checkers/IDE; avoids circular imports at runtime
    from models.document import Document
    from models.user import User


class Source(Base):
    __tablename__ = "sources"
    # Level 1 fix: the same source can't be stored twice.
    __table_args__ = (
        UniqueConstraint(
            "source_type",
            "source_identifier",
            name="uq_sources_type_identifier",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id")
    )
    source_type: Mapped[str] = mapped_column(String(50))
    source_identifier: Mapped[str] = mapped_column(
        String(500), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User | None"] = relationship(
        back_populates="sources"
    )
    document: Mapped["Document | None"] = relationship(
        back_populates="source", uselist=False
    )
