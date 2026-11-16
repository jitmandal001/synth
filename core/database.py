# Level 2: moved from db.py to core/database.py. It's infrastructure (like config),
# so it lives in core/. Contents unchanged; only import paths elsewhere changed.
from collections.abc import AsyncGenerator
# SQLAlchemy -> Connects Python code to the database so you can query, write, and map tables to Python classes.
# alembic -> Handles database migrations, allowing you to version control your database schema changes.
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from core.config import get_settings

# Level 2: the URL comes from Settings, which already fails at startup if it's
# missing, so the old load_dotenv/os.getenv/RuntimeError check isn't needed.
settings = get_settings()

# Create the asynchronous database engine 	Creates the connection engine to PostgreSQL.
engine = create_async_engine(
    settings.database_url.get_secret_value(),
    pool_pre_ping=True,
    echo=False,
)

# Create a reusable session factory
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Base class for all SQLAlchemy models
class Base(DeclarativeBase):
    pass


# Provide a database session to FastAPI endpoints
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session