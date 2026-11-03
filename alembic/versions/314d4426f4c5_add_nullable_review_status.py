
"""add nullable review status

Revision ID: 314d4426f4c5
Revises: 2be01df44ef8
Create Date: 2026-11-03 01:33:39.775679
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '314d4426f4c5'
down_revision: Union[str, Sequence[str], None] = '2be01df44ef8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


review_status_enum = postgresql.ENUM(
    'pending',
    'approved',
    'rejected',
    name='review_status',
    create_type=False,
)


def upgrade() -> None:
    # Create the PostgreSQL enum type.
    review_status_enum.create(op.get_bind(), checkfirst=True)

    # Add the nullable column to extractions.
    op.add_column(
        'extractions',
        sa.Column(
            'review_status',
            review_status_enum,
            nullable=True,
        ),
    )


def downgrade() -> None:
    # Remove the column first.
    op.drop_column('extractions', 'review_status')

    # Then remove the PostgreSQL enum type.
    review_status_enum.drop(op.get_bind(), checkfirst=True)

