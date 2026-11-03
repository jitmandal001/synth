"""backfill review status

Revision ID: 2edae444550d
Revises: 314d4426f4c5
Create Date: 2026-11-03 01:49:56.842299

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2edae444550d'
down_revision: Union[str, Sequence[str], None] = '314d4426f4c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE extractions
        SET review_status = 'pending'
        WHERE review_status IS NULL
        """
    )


def downgrade() -> None:
    pass