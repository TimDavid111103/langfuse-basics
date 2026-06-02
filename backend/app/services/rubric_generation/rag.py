import json

from langfuse import get_client, observe
from openai import OpenAI

from app.schemas.retrieval import RetrievedChunk
from app.schemas.rubric import GeneratedRubric, QuestionItem, RubricCriterion
from app.services.rubric_generation.prompts import RAG_USER_TEMPLATE, RUBRIC_SYSTEM_PROMPT

MODEL = "gpt-4o"


def _format_chunks(chunks: list[RetrievedChunk]) -> str:
    """Format retrieved chunks into a readable passage block for the prompt."""
    parts = []
    for i, chunk in enumerate(chunks, 1):
        header = f"[Passage {i}"
        if chunk.section_title:
            header += f" — {chunk.section_title}"
        if chunk.page_number:
            header += f", p.{chunk.page_number}"
        header += "]"
        parts.append(f"{header}\n{chunk.text}")
    return "\n\n".join(parts)


@observe(name="rubric_rag_generation")
def generate_rubric_rag(
    question: QuestionItem,
    chunks: list[RetrievedChunk],
    client: OpenAI,
) -> GeneratedRubric:
    """Generate a rubric for a question grounded in retrieved source material passages."""
    user_content = RAG_USER_TEMPLATE.format(
        question_text=question.text,
        retrieved_chunks=_format_chunks(chunks),
        expected_concepts=", ".join(question.expected_concepts),
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": RUBRIC_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        response_format={"type": "json_object"},
        max_tokens=2048,
    )

    raw = json.loads(response.choices[0].message.content or "{}")
    criteria = [RubricCriterion(**c) for c in raw["criteria"]]
    lf = get_client()
    span_id = lf.get_current_observation_id() or ""

    usage = response.usage
    prompt_tokens = usage.prompt_tokens if usage else 0
    completion_tokens = usage.completion_tokens if usage else 0

    lf.update_current_generation(
        input={
            "question": question.text,
            "condition": "rag",
            "chunks_used": len(chunks),
        },
        output={"criteria_count": len(criteria), "total_points": raw["total_points"]},
        metadata={"model": MODEL, "question_index": question.index},
    )

    return GeneratedRubric(
        question_index=question.index,
        question_text=question.text,
        criteria=criteria,
        total_points=raw["total_points"],
        condition="rag",
        model_id=MODEL,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cache_read_tokens=0,
        langfuse_span_id=span_id,
    )
