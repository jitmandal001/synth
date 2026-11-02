"""make review status non nullable

Revision ID: a602e0a7ccd0
Revises: 2edae444550d
Create Date: 2026-11-03 01:55:39.642547

"""
from typing import Sequence, Union
from sqlalchemy.dialects import postgresql
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a602e0a7ccd0'
down_revision: Union[str, Sequence[str], None] = '2edae444550d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "extractions",
        "review_status",
        existing_type=postgresql.ENUM(
            "pending",
            "approved",
            "rejected",
            name="review_status",
            create_type=False,
        ),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "extractions",
        "review_status",
        existing_type=postgresql.ENUM(
            "pending",
            "approved",
            "rejected",
            name="review_status",
            create_type=False,
        ),
        nullable=True,
    )
