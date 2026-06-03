import json

from langfuse import get_client, observe
from openai import OpenAI

from app.schemas.retrieval import RetrievedChunk
from app.schemas.rubric import GeneratedRubric, QuestionItem, RubricCriterion
from app.services.rubric_generation.prompts import RAG_USER_TEMPLATE, RUBRIC_SYSTEM_PROMPT

MODEL = "gpt-4o-mini"


def _format_chunks(chunks: list[RetrievedChunk]) -> str:
    """Format retrieved chunks into a numbered passage block for the prompt.

    Each passage includes its section header, the one-sentence context (if
    present), and the raw chunk text so the model has both provenance and
    meaning signals.
    """
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


@observe(name="rubric_rag", as_type="generation", capture_input=False, capture_output=False)
def generate_rubric_rag(
    question: QuestionItem,
    chunks: list[RetrievedChunk],
    client: OpenAI,
) -> GeneratedRubric:
    """Generate a grading rubric grounded in retrieved passages from the source material.

    This is the RAG condition. The retrieved chunks anchor the rubric to the
    specific terminology, equations, and derivations used in the lecture notes,
    rather than relying on the model's prior knowledge.
    """
    user_content = RAG_USER_TEMPLATE.format(
        question_text=question.text,
        retrieved_chunks=_format_chunks(chunks),
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
    usage = response.usage

    get_client().update_current_generation(
        model=MODEL,
        input={
            "question_text": question.text,
            "question_index": question.index,
            "condition": "rag",
            "chunks_used": len(chunks),
        },
        output={"criteria_count": len(criteria), "total_points": raw["total_points"]},
        usage_details={
            "input_tokens": usage.prompt_tokens if usage else 0,
            "output_tokens": usage.completion_tokens if usage else 0,
        },
    )

    return GeneratedRubric(
        question_index=question.index,
        question_text=question.text,
        criteria=criteria,
        total_points=raw["total_points"],
        condition="rag",
        model_id=MODEL,
        prompt_tokens=usage.prompt_tokens if usage else 0,
        completion_tokens=usage.completion_tokens if usage else 0,
    )
