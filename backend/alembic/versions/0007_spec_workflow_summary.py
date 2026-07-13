"""outcome_specs.workflow_summary for proposal parity

Revision ID: 0007_spec_workflow_summary
Revises: 0006_matcher_chat
Create Date: 2026-07-13
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007_spec_workflow_summary"
down_revision: Union[str, None] = "0006_matcher_chat"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = {c["name"] for c in inspector.get_columns("outcome_specs")}
    if "workflow_summary" not in cols:
        op.add_column(
            "outcome_specs",
            sa.Column("workflow_summary", sa.Text(), nullable=False, server_default=""),
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = {c["name"] for c in inspector.get_columns("outcome_specs")}
    if "workflow_summary" in cols:
        op.drop_column("outcome_specs", "workflow_summary")
