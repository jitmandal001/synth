"""seed roles and permissions

Revision ID: 1d3e21a001be
Revises: 618bb3862d38
Create Date: 2026-11-25 00:06:19.905463

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1d3e21a001be'
down_revision: Union[str, Sequence[str], None] = '618bb3862d38'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Level 3: starting roles and permissions as DATA, so every database
# gets the same set from `alembic upgrade head`.
ROLES = ["contributor", "curator", "admin"]

PERMISSIONS = [
    "read:document",       # GET /documents
    "ingest:document",     # POST /extract
    "review:extraction",   # approve / reject extractions
    "manage:users",        # create users, assign roles
    "view:config",         # GET /config-check
]

# Which role gets which permissions. Routes will only ever check
# the permission name, never the role name.
GRANTS = {
    "contributor": ["read:document", "ingest:document"],
    "curator": ["read:document", "review:extraction"],
    "admin": PERMISSIONS,
}

# Frozen descriptions of just the columns we touch. Don't import models/:
# models change later, but this migration must keep working as written.
roles_table = sa.table("roles", sa.column("name", sa.String))
permissions_table = sa.table("permissions", sa.column("name", sa.String))


def upgrade() -> None:
    """Insert the starting roles, permissions and the links between them."""
    op.bulk_insert(roles_table, [{"name": name} for name in ROLES])
    op.bulk_insert(permissions_table, [{"name": name} for name in PERMISSIONS])

    # Link by NAME (ids can differ between databases): find both ids and insert the pair.
    for role, perms in GRANTS.items():
        for perm in perms:
            op.execute(
                sa.text(
                    "INSERT INTO role_permissions (role_id, permission_id) "
                    "SELECT r.id, p.id FROM roles r, permissions p "
                    "WHERE r.name = :role AND p.name = :perm"
                ).bindparams(role=role, perm=perm)
            )


def downgrade() -> None:
    """Remove exactly what upgrade() added."""
    # role_permissions rows go too: their foreign keys are ON DELETE CASCADE.
    op.execute(roles_table.delete().where(roles_table.c.name.in_(ROLES)))
    op.execute(permissions_table.delete().where(permissions_table.c.name.in_(PERMISSIONS)))
