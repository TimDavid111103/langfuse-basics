"""rename questions_json to questions_md

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-02
"""
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("questionnaire_version", "questions_json", new_column_name="questions_md")


def downgrade() -> None:
    op.alter_column("questionnaire_version", "questions_md", new_column_name="questions_json")
