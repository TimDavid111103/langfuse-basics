from pydantic import Field

from app.schemas.base import CamelModel


class RetrievalSearchRequest(CamelModel):
    """Request body for an ad-hoc retrieval search."""

    query: str
    source_material_id: int
    top_k: int = Field(default=5, ge=1, le=20)


class RetrievedChunk(CamelModel):
    """A single chunk returned by vector similarity search."""

    chunk_id: int
    source_material_id: int
    chunk_index: int
    page_number: int | None
    section_title: str | None
    text: str
    # One-sentence context generated at ingest time; null for legacy chunks.
    context: str | None
    cosine_distance: float
