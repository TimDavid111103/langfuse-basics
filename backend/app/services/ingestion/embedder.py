from openai import OpenAI
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.config import settings
from app.models.source_material import MaterialChunk, SourceMaterial
from app.services.ingestion.chunker import TextChunk

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536
BATCH_SIZE = 100

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.openai_api_key)
    return _client


def _embed_texts(texts: list[str]) -> list[list[float]]:
    client = _get_client()
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in response.data]


async def embed_and_store(
    chunks: list[TextChunk],
    source_material_id: int,
    session: AsyncSession,
) -> int:
    all_embeddings: list[list[float]] = []

    for batch_start in range(0, len(chunks), BATCH_SIZE):
        batch_texts = [c.text for c in chunks[batch_start : batch_start + BATCH_SIZE]]
        all_embeddings.extend(_embed_texts(batch_texts))

    db_chunks = [
        MaterialChunk(
            source_material_id=source_material_id,
            page_number=chunk.page_number,
            section_title=chunk.section_title,
            chunk_index=chunk.chunk_index,
            token_count=chunk.token_count,
            text=chunk.text,
            text_preview=chunk.text_preview,
            embedding=embedding,
        )
        for chunk, embedding in zip(chunks, all_embeddings, strict=True)
    ]

    session.add_all(db_chunks)
    await session.flush()

    result = await session.exec(
        select(SourceMaterial).where(SourceMaterial.id == source_material_id)
    )
    material = result.one()
    material.chunk_count = len(db_chunks)
    session.add(material)

    return len(db_chunks)
