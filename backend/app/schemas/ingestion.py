from app.models.source_material import IngestionStatus, MaterialType
from app.schemas.base import CamelModel


class SourceMaterialRead(CamelModel):
    id: int
    name: str
    original_filename: str
    material_type: MaterialType
    page_count: int | None
    chunk_count: int
    ingestion_status: IngestionStatus
    ingestion_error: str | None


class SourceMaterialCreate(CamelModel):
    name: str
    material_type: MaterialType = MaterialType.PDF
