import json
from typing import Literal

from langfuse import get_client, observe
from openai import OpenAI

from app.judging.formatting import format_passages_for_judge, format_rubric
from app.judging.prompts import JUDGE_SYSTEM_PROMPT, JUDGE_USER_TEMPLATE
from app.judging.schemas import DimensionScore, QuestionEvaluationResult
from app.schemas.retrieval import RetrievedChunk
from app.schemas.rubric import GeneratedRubric, QuestionItem

JUDGE_MODEL = "gpt-4o-mini"


@observe(name="judge_evaluation", as_type="generation", capture_input=False, capture_output=False)
def evaluate_rubrics(
    question: QuestionItem,
    rubric_no_rag: GeneratedRubric,
    rubric_rag: GeneratedRubric,
    reference_chunks: list[RetrievedChunk],
    client: OpenAI,
    run_index: int,
) -> QuestionEvaluationResult:
    """Ask the judge model to score both rubrics against the reference passages."""
    user_content = JUDGE_USER_TEMPLATE.format(
        question_text=question.text,
        reference_passages=format_passages_for_judge(reference_chunks),
        rubric_no_rag=format_rubric(rubric_no_rag),
        rubric_rag=format_rubric(rubric_rag),
    )

    response = client.chat.completions.create(
        model=JUDGE_MODEL,
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        response_format={"type": "json_object"},
        max_tokens=4096,
    )

    raw = json.loads(response.choices[0].message.content or "{}")

    dimension_scores = [DimensionScore(**d) for d in raw["dimension_scores"]]
    winner: Literal["no_rag", "rag", "tie"] = raw["winner"]
    usage = response.usage

    get_client().update_current_generation(
        model=JUDGE_MODEL,
        input=[
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        output={
            "winner": winner,
            "no_rag_total": raw["no_rag_total"],
            "rag_total": raw["rag_total"],
            "dimension_scores": [d.model_dump() for d in dimension_scores],
            "judge_reasoning": raw["judge_reasoning"],
        },
        usage_details={
            "input_tokens": usage.prompt_tokens if usage else 0,
            "output_tokens": usage.completion_tokens if usage else 0,
        },
    )

    return QuestionEvaluationResult(
        run_index=run_index,
        question_index=question.index,
        question_text=question.text,
        dimension_scores=dimension_scores,
        no_rag_total=raw["no_rag_total"],
        rag_total=raw["rag_total"],
        winner=winner,
        judge_reasoning=raw["judge_reasoning"],
        judge_model=JUDGE_MODEL,
    )
