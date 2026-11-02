
from datetime import datetime
import enum
from sqlalchemy import Enum
from sqlalchemy import (
    String,
    Text,
    Integer,
    Float,
    ForeignKey,
    DateTime,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db import Base

class ReviewStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    sources: Mapped[list["Source"]] = relationship(
        back_populates="user"
    )


class Source(Base):
    __tablename__ = "sources"

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


class Extraction(Base):
    __tablename__ = "extractions"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id"), nullable=False
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    key_entities: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer)
    latency: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    document: Mapped["Document"] = relationship(
        back_populates="extractions"
    )
    review_status: Mapped[ReviewStatus | None] = mapped_column(
    Enum(
        ReviewStatus,
        name="review_status",
        values_callable=lambda enum_class: [
            item.value for item in enum_class
        ],
    ),
    nullable=True,
    )