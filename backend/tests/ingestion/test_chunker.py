from app.services.ingestion.chunker import MAX_CHUNK_TOKENS, TextChunk, chunk_pages
from app.services.ingestion.pdf_extractor import PageContent


def _page(
    text: str,
    *,
    page_number: int = 1,
    section_title: str | None = "Introduction",
) -> PageContent:
    return PageContent(
        page_number=page_number,
        section_title=section_title,
        text=text,
    )


class TestChunkPages:
    def test_single_small_page_produces_one_chunk(self) -> None:
        pages = [_page("Short paragraph about fluids.")]
        chunks = chunk_pages(pages)

        assert len(chunks) == 1
        assert chunks[0].text == "Short paragraph about fluids."
        assert chunks[0].section_title == "Introduction"
        assert chunks[0].chunk_index == 0

    def test_section_boundary_starts_new_chunk(self) -> None:
        pages = [
            _page("Section A content.", section_title="Part A"),
            _page("Section B content.", section_title="Part B"),
        ]
        chunks = chunk_pages(pages)

        assert len(chunks) == 2
        assert chunks[0].section_title == "Part A"
        assert chunks[1].section_title == "Part B"

    def test_accumulates_items_until_token_limit(self) -> None:
        short = "Word " * 20
        pages = [_page(short) for _ in range(50)]
        chunks = chunk_pages(pages)

        assert len(chunks) > 1
        for chunk in chunks:
            assert chunk.token_count <= MAX_CHUNK_TOKENS or len(chunks) == 1

    def test_oversized_item_split_at_sentences(self) -> None:
        sentence = "This is a physics sentence about pressure. " * 200
        pages = [_page(sentence.strip())]
        chunks = chunk_pages(pages)

        assert len(chunks) > 1
        assert all(isinstance(c, TextChunk) for c in chunks)

    def test_empty_pages_returns_empty(self) -> None:
        assert chunk_pages([]) == []

    def test_text_preview_truncated(self) -> None:
        long_text = "x" * 500
        chunks = chunk_pages([_page(long_text)])

        assert len(chunks[0].text_preview) == 200
