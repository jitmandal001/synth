import os

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not configured.")

# The engine keeps a pool of open connections to PostgreSQL and reuses them.
engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)

# Each request gets its own session: one conversation with the database.
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    """Parent class for all table models in models.py."""


async def get_db():
    async with SessionLocal() as session:
        yield session
