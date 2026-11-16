# Level 2: models.py split into one file per table.
# Importing the package imports every model, which registers each table on
# Base.metadata. SQLAlchemy needs all of them registered to resolve the
# string relationships ("Source", "Document", ...) and Alembic needs them
# for autogenerate. It also keeps old-style imports working:
#     from models import Source, Document, Extraction, ReviewStatus
from models.user import User
from models.source import Source
from models.document import Document
from models.extraction import Extraction, ReviewStatus

__all__ = ["User", "Source", "Document", "Extraction", "ReviewStatus"]
