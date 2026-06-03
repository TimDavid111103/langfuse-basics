import re
from dataclasses import dataclass

import tiktoken

from app.services.ingestion.pdf_extractor import PageContent

# Target size for a single chunk. Keeps chunks within the embedding model's
# optimal range while preserving enough context for meaningful retrieval.
MAX_CHUNK_TOKENS = 512

_enc = tiktoken.get_encoding("cl100k_base")


@dataclass
class TextChunk:
    """A single semantic chunk ready for embedding and storage."""

    chunk_index: int
    page_number: int | None
    section_title: str | None
    text: str
    token_count: int
    text_preview: str


def _count_tokens(text: str) -> int:
    """Return the cl100k token count for a string."""
    return len(_enc.encode(text))


def _split_at_sentences(text: str, max_tokens: int) -> list[str]:
    """Split text at sentence boundaries to fit within max_tokens.

    Uses a lookbehind on .!? followed by whitespace + uppercase to avoid
    splitting on abbreviations like e.g., i.e., eq.
    Only called as a fallback for single items that exceed MAX_CHUNK_TOKENS.
    """
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)

    result: list[str] = []
    current: list[str] = []
    current_tokens = 0

    for sentence in sentences:
        sentence_tokens = _count_tokens(sentence)
        if current_tokens + sentence_tokens > max_tokens and current:
            result.append(' '.join(current))
            current = [sentence]
            current_tokens = sentence_tokens
        else:
            current.append(sentence)
            current_tokens += sentence_tokens

    if current:
        result.append(' '.join(current))

    return result or [text]


def _make_chunk(index: int, texts: list[str], page: int | None, section: str | None) -> TextChunk:
    """Assemble a TextChunk from accumulated item texts."""
    text = '\n\n'.join(texts)
    token_count = _count_tokens(text)
    return TextChunk(
        chunk_index=index,
        page_number=page,
        section_title=section,
        text=text,
        token_count=token_count,
        text_preview=text[:200],
    )


def chunk_pages(pages: list[PageContent]) -> list[TextChunk]:
    """Group Docling items into semantic chunks.

    Strategy:
    - Items from the same section are accumulated until MAX_CHUNK_TOKENS is reached.
    - A section boundary always closes the current chunk, so content from
      different sections never merges into one chunk.
    - Single items that exceed MAX_CHUNK_TOKENS are split at sentence boundaries
      as a last resort.
    """
    chunks: list[TextChunk] = []
    chunk_index = 0

    current_texts: list[str] = []
    current_tokens = 0
    current_section: str | None = None
    current_page: int | None = None

    def flush() -> None:
        nonlocal chunk_index, current_texts, current_tokens, current_page
        if not current_texts:
            return
        chunks.append(_make_chunk(chunk_index, current_texts, current_page, current_section))
        chunk_index += 1
        current_texts = []
        current_tokens = 0
        current_page = None

    for page in pages:
        item_tokens = _count_tokens(page.text)

        # Section boundary: always start a new chunk.
        if page.section_title != current_section:
            flush()
            current_section = page.section_title

        if current_page is None:
            current_page = page.page_number

        # Oversized single item: flush any pending content, then split by sentence.
        if item_tokens > MAX_CHUNK_TOKENS:
            flush()
            current_page = page.page_number
            for sub_text in _split_at_sentences(page.text, MAX_CHUNK_TOKENS):
                sub_tokens = _count_tokens(sub_text)
                chunks.append(TextChunk(
                    chunk_index=chunk_index,
                    page_number=page.page_number,
                    section_title=page.section_title,
                    text=sub_text,
                    token_count=sub_tokens,
                    text_preview=sub_text[:200],
                ))
                chunk_index += 1
            continue

        # Adding this item would overflow the current chunk: flush first.
        if current_tokens + item_tokens > MAX_CHUNK_TOKENS:
            flush()
            current_page = page.page_number

        current_texts.append(page.text)
        current_tokens += item_tokens

    flush()
    return chunks
