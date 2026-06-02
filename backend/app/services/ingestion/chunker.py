from dataclasses import dataclass

import tiktoken

from app.services.ingestion.pdf_extractor import PageContent

CHUNK_SIZE_TOKENS = 512
OVERLAP_TOKENS = 64

_enc = tiktoken.get_encoding("cl100k_base")


@dataclass
class TextChunk:
    chunk_index: int
    page_number: int | None
    section_title: str | None
    text: str
    token_count: int
    text_preview: str


def _count_tokens(text: str) -> int:
    return len(_enc.encode(text))


def _split_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    tokens = _enc.encode(text)
    if len(tokens) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunks.append(_enc.decode(chunk_tokens))
        if end == len(tokens):
            break
        start += chunk_size - overlap

    return chunks


def chunk_pages(pages: list[PageContent]) -> list[TextChunk]:
    chunks: list[TextChunk] = []
    chunk_index = 0

    for page in pages:
        sub_texts = _split_text(page.text, CHUNK_SIZE_TOKENS, OVERLAP_TOKENS)
        for sub_text in sub_texts:
            token_count = _count_tokens(sub_text)
            chunks.append(
                TextChunk(
                    chunk_index=chunk_index,
                    page_number=page.page_number,
                    section_title=page.section_title,
                    text=sub_text,
                    token_count=token_count,
                    text_preview=sub_text[:200],
                )
            )
            chunk_index += 1

    return chunks
