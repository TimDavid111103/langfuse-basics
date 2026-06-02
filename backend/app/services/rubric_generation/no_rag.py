import json

from langfuse import get_client, observe
from openai import OpenAI

from app.schemas.rubric import GeneratedRubric, QuestionItem, RubricCriterion
from app.services.rubric_generation.prompts import NO_RAG_USER_TEMPLATE, RUBRIC_SYSTEM_PROMPT

MODEL = "gpt-4o"


@observe(name="rubric_no_rag_generation")
def generate_rubric_no_rag(
    question: QuestionItem,
    client: OpenAI,
) -> GeneratedRubric:
    """Generate a rubric for a question using only the model's internal knowledge."""
    user_content = NO_RAG_USER_TEMPLATE.format(
        question_text=question.text,
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
        input={"question": question.text, "condition": "no_rag"},
        output={"criteria_count": len(criteria), "total_points": raw["total_points"]},
        metadata={"model": MODEL, "question_index": question.index},
    )

    return GeneratedRubric(
        question_index=question.index,
        question_text=question.text,
        criteria=criteria,
        total_points=raw["total_points"],
        condition="no_rag",
        model_id=MODEL,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cache_read_tokens=0,
        langfuse_span_id=span_id,
    )
