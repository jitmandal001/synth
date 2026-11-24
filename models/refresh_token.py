from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base

if TYPE_CHECKING:
    from models.user import User


class RefreshToken(Base):
    """One refresh token ever issued. Only its SHA-256 hash is stored."""

    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # sha256 hex = 64 characters. Unique: lookups go by this hash.
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    # Same value for every token that came from one login (rotation chain).
    family_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # NULL = still usable. Set when rotated, logged out, or revoked.
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # The token that replaced this one on refresh (for tracing a chain).
    replaced_by_id: Mapped[int | None] = mapped_column(ForeignKey("refresh_tokens.id"))

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")