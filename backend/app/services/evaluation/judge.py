import json
from typing import Literal

from langfuse import get_client, observe
from openai import OpenAI

from app.config import settings
from app.schemas.evaluation import (
    DimensionScore,
    ExperimentEvaluationSummary,
    QuestionEvaluationResult,
    RunSummary,
)
from app.schemas.retrieval import RetrievedChunk
from app.schemas.rubric import GeneratedRubric, QuestionItem
from app.services.evaluation.prompts import JUDGE_SYSTEM_PROMPT, JUDGE_USER_TEMPLATE

JUDGE_MODEL = "gpt-4o"

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.openai_api_key)
    return _client


def _format_rubric(rubric: GeneratedRubric) -> str:
    lines = []
    for c in rubric.criteria:
        lines.append(
            f"- {c.criterion_name} ({c.point_value} pts): {c.description}\n"
            f"  Correct: {c.example_correct_response}\n"
            f"  Incorrect: {c.example_incorrect_response}"
        )
    return "\n".join(lines)


def _format_passages(chunks: list[RetrievedChunk]) -> str:
    parts = []
    for i, chunk in enumerate(chunks, 1):
        header = f"[{i}"
        if chunk.section_title:
            header += f" — {chunk.section_title}"
        header += "]"
        parts.append(f"{header}\n{chunk.text}")
    return "\n\n".join(parts)


@observe(name="judge_evaluation")
def evaluate_rubrics(
    question: QuestionItem,
    rubric_no_rag: GeneratedRubric,
    rubric_rag: GeneratedRubric,
    reference_chunks: list[RetrievedChunk],
    client: OpenAI,
    run_index: int,
) -> QuestionEvaluationResult:
    user_content = JUDGE_USER_TEMPLATE.format(
        question_text=question.text,
        reference_passages=_format_passages(reference_chunks),
        rubric_no_rag=_format_rubric(rubric_no_rag),
        rubric_rag=_format_rubric(rubric_rag),
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
    lf = get_client()
    span_id = lf.get_current_observation_id() or ""

    dimension_scores = [DimensionScore(**d) for d in raw["dimension_scores"]]
    winner: Literal["no_rag", "rag", "tie"] = raw["winner"]

    lf.update_current_generation(
        input={"question": question.text, "question_index": question.index, "run_index": run_index},
        output={"winner": winner, "no_rag_total": raw["no_rag_total"], "rag_total": raw["rag_total"]},
        metadata={"model": JUDGE_MODEL},
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
        langfuse_span_id=span_id,
    )


def _run_winner(no_rag: float, rag: float) -> Literal["no_rag", "rag", "tie"]:
    if rag > no_rag:
        return "rag"
    if no_rag > rag:
        return "no_rag"
    return "tie"


def aggregate_results(
    experiment_id: int,
    runs: list[list[QuestionEvaluationResult]],
) -> ExperimentEvaluationSummary:
    num_runs = len(runs)

    run_summaries: list[RunSummary] = []
    for run_idx, run_results in enumerate(runs):
        n = len(run_results)
        no_rag_avg = sum(r.no_rag_total for r in run_results) / n
        rag_avg = sum(r.rag_total for r in run_results) / n
        run_summaries.append(
            RunSummary(
                run_index=run_idx,
                per_question_results=run_results,
                no_rag_avg=no_rag_avg,
                rag_avg=rag_avg,
                winner=_run_winner(no_rag_avg, rag_avg),
            )
        )

    all_results = [r for run in runs for r in run]
    overall_no_rag = sum(r.no_rag_total for r in all_results) / len(all_results)
    overall_rag = sum(r.rag_total for r in all_results) / len(all_results)

    dimensions = ["concept_coverage", "factual_accuracy", "specificity", "subject_matter_depth"]
    dimension_averages: dict[str, dict[Literal["no_rag", "rag"], float]] = {}
    for dim in dimensions:
        no_rag_scores = [d.rubric_no_rag_score for r in all_results for d in r.dimension_scores if d.dimension == dim]
        rag_scores = [d.rubric_rag_score for r in all_results for d in r.dimension_scores if d.dimension == dim]
        dimension_averages[dim] = {
            "no_rag": sum(no_rag_scores) / len(no_rag_scores) if no_rag_scores else 0.0,
            "rag": sum(rag_scores) / len(rag_scores) if rag_scores else 0.0,
        }

    rag_wins = sum(1 for rs in run_summaries if rs.winner == "rag")
    no_rag_wins = sum(1 for rs in run_summaries if rs.winner == "no_rag")
    ties = num_runs - rag_wins - no_rag_wins

    judge_summary = (
        f"Aggregate over {num_runs} run(s): overall winner = {_run_winner(overall_no_rag, overall_rag)}. "
        f"Run-level wins — RAG: {rag_wins}, No-RAG: {no_rag_wins}, Tie: {ties}. "
        f"Avg scores — No-RAG: {overall_no_rag:.2f}, RAG: {overall_rag:.2f} (max 40)."
    )

    return ExperimentEvaluationSummary(
        experiment_id=experiment_id,
        num_runs=num_runs,
        runs=run_summaries,
        overall_no_rag_score=overall_no_rag,
        overall_rag_score=overall_rag,
        overall_winner=_run_winner(overall_no_rag, overall_rag),
        dimension_averages=dimension_averages,
        judge_summary=judge_summary,
    )
