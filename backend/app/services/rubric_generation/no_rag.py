import json

from langfuse import get_client, observe
from openai import OpenAI

from app.schemas.rubric import GeneratedRubric, QuestionItem, RubricCriterion
from app.services.rubric_generation.prompts import NO_RAG_USER_TEMPLATE, RUBRIC_SYSTEM_PROMPT

MODEL = "gpt-4o-mini"


@observe(name="rubric_no_rag", as_type="generation", capture_input=False, capture_output=False)
def generate_rubric_no_rag(
    question: QuestionItem,
    client: OpenAI,
) -> GeneratedRubric:
    """Generate a grading rubric using only the model's internal knowledge (no retrieved context).

    This is the baseline condition. The rubric reflects whatever the model
    knows about the topic without any grounding in the specific source material.
    """
    user_content = NO_RAG_USER_TEMPLATE.format(question_text=question.text)

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
        input={"question_text": question.text, "question_index": question.index, "condition": "no_rag"},
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
        condition="no_rag",
        model_id=MODEL,
        prompt_tokens=usage.prompt_tokens if usage else 0,
        completion_tokens=usage.completion_tokens if usage else 0,
    )
