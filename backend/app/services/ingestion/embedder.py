from openai import OpenAI
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings
from app.models.source_material import MaterialChunk, SourceMaterial
from app.services.ingestion.chunker import TextChunk

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536
CONTEXT_MODEL = "gpt-4o-mini"
# How many chunks to send to the embedding API in a single request.
BATCH_SIZE = 100

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    """Return the shared OpenAI client, creating it on first call."""
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.openai_api_key)
    return _client


def _generate_context(doc_title: str, chunk: TextChunk) -> str:
    """Generate a one-sentence context that situates this chunk within its document.

    The context is prepended to the chunk text before embedding (contextual
    retrieval), which improves semantic search by anchoring each chunk to its
    role in the broader document.
    """
    section = chunk.section_title or "General"
    prompt = (
        f"You are indexing a physics lecture document titled \"{doc_title}\".\n"
        f"Section: {section}\n\n"
        f"Passage:\n{chunk.text}\n\n"
        "Write a single sentence (≤20 words) situating this passage within the broader document. "
        "Output only the sentence, no preamble."
    )
    response = _get_client().chat.completions.create(
        model=CONTEXT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=60,
        temperature=0.0,
    )
    return (response.choices[0].message.content or "").strip()


def _embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of strings and return the resulting float vectors."""
    response = _get_client().embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in response.data]


async def embed_and_store(
    chunks: list[TextChunk],
    source_material_id: int,
    session: AsyncSession,
) -> int:
    """Generate contexts and embeddings for all chunks, then persist them.

    For each chunk:
    1. An LLM generates a one-sentence context string.
    2. The embedding is computed over context + text (not text alone), which
       grounds the vector in the chunk's role within the document.
    3. Both the raw text and the context are stored separately so retrieved
       chunks can surface the context to downstream prompts.

    Returns the number of chunks stored.
    """
    result = await session.exec(
        select(SourceMaterial).where(SourceMaterial.id == source_material_id)
    )
    material = result.one()
    doc_title = material.name

    contexts = [_generate_context(doc_title, chunk) for chunk in chunks]

    # Embed context + text so that retrieval is anchored to the chunk's role,
    # not just its surface content.
    embed_inputs = [
        f"{context}\n\n{chunk.text}"
        for context, chunk in zip(contexts, chunks, strict=True)
    ]

    all_embeddings: list[list[float]] = []
    for batch_start in range(0, len(embed_inputs), BATCH_SIZE):
        batch = embed_inputs[batch_start : batch_start + BATCH_SIZE]
        all_embeddings.extend(_embed_texts(batch))

    db_chunks = [
        MaterialChunk(
            source_material_id=source_material_id,
            page_number=chunk.page_number,
            section_title=chunk.section_title,
            chunk_index=chunk.chunk_index,
            token_count=chunk.token_count,
            text=chunk.text,
            context=context,
            text_preview=chunk.text_preview,
            embedding=embedding,
        )
        for chunk, context, embedding in zip(chunks, contexts, all_embeddings, strict=True)
    ]

    session.add_all(db_chunks)
    await session.flush()

    material.chunk_count = len(db_chunks)
    session.add(material)

    return len(db_chunks)
