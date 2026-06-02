from pydantic import Field

from app.schemas.base import CamelModel


class RetrievalSearchRequest(CamelModel):
    query: str
    source_material_id: int
    top_k: int = Field(default=5, ge=1, le=20)


class RetrievedChunk(CamelModel):
    chunk_id: int
    source_material_id: int
    chunk_index: int
    page_number: int | None
    section_title: str | None
    text: str
    cosine_distance: float
