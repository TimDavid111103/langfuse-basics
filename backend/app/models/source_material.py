from datetime import datetime
from enum import StrEnum
from typing import Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, Text
from sqlmodel import Field, SQLModel


class IngestionStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"


class MaterialType(StrEnum):
    PDF = "pdf"
    SLIDES = "slides"
    NOTES = "notes"
    OTHER = "other"


class SourceMaterial(SQLModel, table=True):
    """A single uploaded document (e.g. lecture PDF) that has been ingested."""

    __tablename__ = "source_material"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    filename: str
    original_filename: str
    # SHA-256 of the file bytes, used to skip re-ingestion of identical files.
    file_hash: str = Field(unique=True)
    material_type: MaterialType = Field(default=MaterialType.PDF)
    page_count: Optional[int] = Field(default=None)
    chunk_count: int = Field(default=0)
    ingestion_status: IngestionStatus = Field(default=IngestionStatus.PENDING)
    ingestion_error: Optional[str] = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class MaterialChunk(SQLModel, table=True):
    """A single semantic chunk of a source document with its embedding."""

    __tablename__ = "material_chunk"

    id: Optional[int] = Field(default=None, primary_key=True)
    source_material_id: int = Field(foreign_key="source_material.id", index=True)
    page_number: Optional[int] = Field(default=None)
    section_title: Optional[str] = Field(default=None)
    chunk_index: int
    token_count: int
    text: str = Field(sa_column=Column(Text, nullable=False))
    # One-sentence context generated at ingest time that situates this chunk
    # within the broader document; prepended to text before embedding.
    context: Optional[str] = Field(default=None, sa_column=Column(Text))
    text_preview: str
    # 1536-dimensional vector from text-embedding-3-small; indexed via HNSW.
    embedding: Optional[list[float]] = Field(
        default=None, sa_column=Column(Vector(1536))
    )
