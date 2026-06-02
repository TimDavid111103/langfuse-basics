"""initial

Revision ID: 0001
Revises:
Create Date: 2026-06-02

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "source_material",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sqlmodel.AutoString(), nullable=False),
        sa.Column("filename", sqlmodel.AutoString(), nullable=False),
        sa.Column("original_filename", sqlmodel.AutoString(), nullable=False),
        sa.Column("file_hash", sqlmodel.AutoString(), nullable=False, unique=True),
        sa.Column("material_type", sqlmodel.AutoString(), nullable=False, server_default="pdf"),
        sa.Column("page_count", sa.Integer, nullable=True),
        sa.Column("chunk_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("ingestion_status", sqlmodel.AutoString(), nullable=False, server_default="pending"),
        sa.Column("ingestion_error", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "material_chunk",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("source_material_id", sa.Integer, sa.ForeignKey("source_material.id"), nullable=False),
        sa.Column("page_number", sa.Integer, nullable=True),
        sa.Column("section_title", sqlmodel.AutoString(), nullable=True),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("token_count", sa.Integer, nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("text_preview", sqlmodel.AutoString(), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=True),
    )
    op.create_index("ix_material_chunk_source_material_id", "material_chunk", ["source_material_id"])
    op.execute(
        "CREATE INDEX ix_material_chunk_embedding ON material_chunk USING hnsw (embedding vector_cosine_ops)"
    )

    op.create_table(
        "questionnaire",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sqlmodel.AutoString(), nullable=False),
        sa.Column("description", sqlmodel.AutoString(), nullable=False),
        sa.Column("source_material_id", sa.Integer, sa.ForeignKey("source_material.id"), nullable=True),
        sa.Column("current_version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_questionnaire_source_material_id", "questionnaire", ["source_material_id"])

    op.create_table(
        "questionnaire_version",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("questionnaire_id", sa.Integer, sa.ForeignKey("questionnaire.id"), nullable=False),
        sa.Column("version_number", sa.Integer, nullable=False),
        sa.Column("questions_json", sa.Text, nullable=False),
        sa.Column("change_summary", sqlmodel.AutoString(), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_questionnaire_version_questionnaire_id", "questionnaire_version", ["questionnaire_id"])

    op.create_table(
        "experiment",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sqlmodel.AutoString(), nullable=False),
        sa.Column("questionnaire_id", sa.Integer, sa.ForeignKey("questionnaire.id"), nullable=False),
        sa.Column("questionnaire_version", sa.Integer, nullable=False),
        sa.Column("source_material_id", sa.Integer, sa.ForeignKey("source_material.id"), nullable=False),
        sa.Column("status", sqlmodel.AutoString(), nullable=False, server_default="created"),
        sa.Column("langfuse_trace_id", sqlmodel.AutoString(), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("completed_at", sa.DateTime, nullable=True),
    )
    op.create_index("ix_experiment_questionnaire_id", "experiment", ["questionnaire_id"])
    op.create_index("ix_experiment_source_material_id", "experiment", ["source_material_id"])

    op.create_table(
        "experiment_result",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("experiment_id", sa.Integer, sa.ForeignKey("experiment.id"), nullable=False),
        sa.Column("question_index", sa.Integer, nullable=False),
        sa.Column("question_text", sa.Text, nullable=False),
        sa.Column("rubric_no_rag", sa.Text, nullable=False),
        sa.Column("rubric_rag", sa.Text, nullable=False),
        sa.Column("retrieved_chunks_json", sa.Text, nullable=False),
        sa.Column("evaluation_json", sa.Text, nullable=True),
        sa.Column("winner", sqlmodel.AutoString(), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_experiment_result_experiment_id", "experiment_result", ["experiment_id"])


def downgrade() -> None:
    op.drop_table("experiment_result")
    op.drop_table("experiment")
    op.drop_table("questionnaire_version")
    op.drop_table("questionnaire")
    op.drop_table("material_chunk")
    op.drop_table("source_material")
