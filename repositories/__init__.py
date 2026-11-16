# Level 2: repositories are the only code that talks to the database.
# Routes and services call plain methods ("list documents in cs.CL") and never
# build select()/join/commit themselves. Swapping Postgres for another database
# (e.g. SQLite in tests) should only need changes here and in core/config.py.
from repositories.document_repository import DocumentRepository

__all__ = ["DocumentRepository"]
