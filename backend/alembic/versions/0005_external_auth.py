"""add users.external_auth_id for Clerk subject

Revision ID: 0005_external_auth
Revises: 0004_lifecycle_tables
Create Date: 2026-07-12
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005_external_auth"
down_revision: Union[str, None] = "0004_lifecycle_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = {c["name"] for c in inspector.get_columns("users")}
    if "external_auth_id" not in cols:
        op.add_column(
            "users",
            sa.Column("external_auth_id", sa.String(128), nullable=True),
        )
        op.create_index("ix_users_external_auth_id", "users", ["external_auth_id"], unique=True)


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = {c["name"] for c in inspector.get_columns("users")}
    if "external_auth_id" in cols:
        op.drop_index("ix_users_external_auth_id", table_name="users")
        op.drop_column("users", "external_auth_id")
