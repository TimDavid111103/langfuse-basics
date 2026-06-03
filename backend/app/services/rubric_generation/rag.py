import json

from langfuse import get_client, observe
from openai import OpenAI

from app.eval.formatting import format_chunks_for_rubric
from app.schemas.retrieval import RetrievedChunk
from app.schemas.rubric import GeneratedRubric, QuestionItem, RubricCriterion
from app.services.rubric_generation.prompts import RAG_USER_TEMPLATE, RUBRIC_SYSTEM_PROMPT

MODEL = "gpt-4o-mini"


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
        retrieved_chunks=format_chunks_for_rubric(chunks),
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
        input=[
            {"role": "system", "content": RUBRIC_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        output={"criteria": [c.model_dump() for c in criteria], "total_points": raw["total_points"]},
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
