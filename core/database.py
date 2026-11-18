# Level 2: moved from db.py to core/database.py. It's infrastructure (like config),
# so it lives in core/. Contents unchanged; only import paths elsewhere changed.
#
# POST /extract path, step 5 of 10: get_db() opens the session this request uses.
# The engine and SessionLocal below are created once, at startup.
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
settings = get_settings()                         # read .env once (cached)

# Create the asynchronous database engine 	Creates the connection engine to PostgreSQL.
engine = create_async_engine(                     # connection pool, made once at startup
    settings.database_url.get_secret_value(),     # the real postgresql+asyncpg://... URL
    pool_pre_ping=True,                           # test a pooled connection before using it
    echo=False,                                   # True would print every SQL statement
)

# Create a reusable session factory
SessionLocal = async_sessionmaker(                # calling SessionLocal() gives a new session
    bind=engine,                                  # sessions borrow connections from the pool
    class_=AsyncSession,                          # async version (use await)
    expire_on_commit=False,                       # keep values readable after commit
)


# Base class for all SQLAlchemy models
class Base(DeclarativeBase):
    pass


# Provide a database session to FastAPI endpoints
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:         # open a session for this request
        yield session                             # hand it out; after the response, it closes
