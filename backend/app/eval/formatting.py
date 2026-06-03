from app.schemas.retrieval import RetrievedChunk
from app.schemas.rubric import GeneratedRubric


def format_rubric(rubric: GeneratedRubric) -> str:
    """Render a rubric as a human-readable bullet list for the judge prompt."""
    lines = []
    for c in rubric.criteria:
        lines.append(
            f"- {c.criterion_name} ({c.point_value} pts): {c.description}\n"
            f"  Correct: {c.example_correct_response}\n"
            f"  Incorrect: {c.example_incorrect_response}"
        )
    return "\n".join(lines)


def format_chunks_for_rubric(chunks: list[RetrievedChunk]) -> str:
    """Format retrieved chunks for rubric-generation prompts."""
    parts = []
    for i, chunk in enumerate(chunks, 1):
        header = f"[Passage {i}"
        if chunk.section_title:
            header += f" — {chunk.section_title}"
        if chunk.page_number:
            header += f", p.{chunk.page_number}"
        header += "]"
        body = f"{header}\n"
        if chunk.context:
            body += f"Context: {chunk.context}\n"
        body += chunk.text
        parts.append(body)
    return "\n\n".join(parts)


def format_passages_for_judge(chunks: list[RetrievedChunk]) -> str:
    """Format retrieved chunks as reference passages for the judge prompt."""
    parts = []
    for i, chunk in enumerate(chunks, 1):
        header = f"[{i}"
        if chunk.section_title:
            header += f" — {chunk.section_title}"
        header += "]"
        body = f"{header}\n"
        if chunk.context:
            body += f"Context: {chunk.context}\n"
        body += chunk.text
        parts.append(body)
    return "\n\n".join(parts)
