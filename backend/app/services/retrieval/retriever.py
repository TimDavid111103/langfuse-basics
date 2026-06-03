import asyncio

from openai import OpenAI
from sqlalchemy import text
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings
from app.schemas.retrieval import RetrievedChunk
from app.services.ingestion.embedder import EMBEDDING_MODEL

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    """Return the shared OpenAI client, creating it on first call."""
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.openai_api_key)
    return _client


def _embed_query(query: str) -> list[float]:
    """Embed a query string using the same model used during ingestion."""
    response = _get_client().embeddings.create(model=EMBEDDING_MODEL, input=query)
    return response.data[0].embedding


async def retrieve_chunks(
    query: str,
    source_material_id: int,
    top_k: int,
    session: AsyncSession,
) -> list[RetrievedChunk]:
    """Return the top_k most semantically similar chunks for a query.

    The query is embedded on a thread to avoid blocking the event loop, then
    compared against all chunks for the given source material using cosine
    distance via pgvector's <=> operator.
    """
    query_embedding = await asyncio.to_thread(_embed_query, query)
    # pgvector requires the vector as a bracketed comma-separated string.
    embedding_str = "[" + ",".join(str(v) for v in query_embedding) + "]"

    rows = await session.execute(
        text(
            """
            SELECT
                id,
                source_material_id,
                chunk_index,
                page_number,
                section_title,
                text,
                context,
                embedding <=> CAST(:embedding AS vector) AS cosine_distance
            FROM material_chunk
            WHERE source_material_id = :source_material_id
            ORDER BY cosine_distance ASC
            LIMIT :top_k
            """
        ),
        {
            "embedding": embedding_str,
            "source_material_id": source_material_id,
            "top_k": top_k,
        },
    )

    return [
        RetrievedChunk(
            chunk_id=row.id,
            source_material_id=row.source_material_id,
            chunk_index=row.chunk_index,
            page_number=row.page_number,
            section_title=row.section_title,
            text=row.text,
            context=row.context,
            cosine_distance=float(row.cosine_distance),
        )
        for row in rows
    ]
