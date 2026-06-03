"""re-add langfuse_trace_id to experiment

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-03

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("experiment", sa.Column("langfuse_trace_id", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("experiment", "langfuse_trace_id")
