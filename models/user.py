from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String, func, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base

if TYPE_CHECKING:  # only for type checkers/IDE; avoids circular imports at runtime
    from models.source import Source
    from models.refresh_token import RefreshToken
    from models.role import Role

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    # Level 3: Argon2 hash of the password, never the password itself.
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    # Level 3: False = account disabled (can't log in, tokens rejected).
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=true()
    )
    sources: Mapped[list["Source"]] = relationship(
        back_populates="user"
    )
        # Level 3: many-to-many through the user_roles link table.
    roles: Mapped[list["Role"]] = relationship(
        secondary="user_roles", back_populates="users"
    )
    # Level 3: every refresh token issued to this user.
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )