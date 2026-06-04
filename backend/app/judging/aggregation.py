from typing import Literal

from app.judging.schemas import ExperimentEvaluationSummary, QuestionEvaluationResult, RunSummary

EVAL_DIMENSIONS = (
    "concept_coverage",
    "factual_accuracy",
    "specificity",
    "subject_matter_depth",
)


def run_winner(no_rag: float, rag: float) -> Literal["no_rag", "rag", "tie"]:
    """Determine the winning condition for a single run or overall."""
    if rag > no_rag:
        return "rag"
    if no_rag > rag:
        return "no_rag"
    return "tie"


def aggregate_results(
    experiment_id: int,
    runs: list[list[QuestionEvaluationResult]],
) -> ExperimentEvaluationSummary:
    """Aggregate per-question judge results across all runs into a summary."""
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
                winner=run_winner(no_rag_avg, rag_avg),
            )
        )

    all_results = [r for run in runs for r in run]
    overall_no_rag = sum(r.no_rag_total for r in all_results) / len(all_results)
    overall_rag = sum(r.rag_total for r in all_results) / len(all_results)

    dimension_averages: dict[str, dict[Literal["no_rag", "rag"], float]] = {}
    for dim in EVAL_DIMENSIONS:
        no_rag_scores = [
            d.rubric_no_rag_score
            for r in all_results
            for d in r.dimension_scores
            if d.dimension == dim
        ]
        rag_scores = [
            d.rubric_rag_score
            for r in all_results
            for d in r.dimension_scores
            if d.dimension == dim
        ]
        dimension_averages[dim] = {
            "no_rag": sum(no_rag_scores) / len(no_rag_scores) if no_rag_scores else 0.0,
            "rag": sum(rag_scores) / len(rag_scores) if rag_scores else 0.0,
        }

    rag_wins = sum(1 for rs in run_summaries if rs.winner == "rag")
    no_rag_wins = sum(1 for rs in run_summaries if rs.winner == "no_rag")
    ties = num_runs - rag_wins - no_rag_wins

    overall_winner = run_winner(overall_no_rag, overall_rag)
    judge_summary = (
        f"Aggregate over {num_runs} run(s): overall winner = {overall_winner}. "
        f"Run-level wins — RAG: {rag_wins}, No-RAG: {no_rag_wins}, Tie: {ties}. "
        f"Avg scores — No-RAG: {overall_no_rag:.2f}, RAG: {overall_rag:.2f} (max 40)."
    )

    return ExperimentEvaluationSummary(
        experiment_id=experiment_id,
        num_runs=num_runs,
        runs=run_summaries,
        overall_no_rag_score=overall_no_rag,
        overall_rag_score=overall_rag,
        overall_winner=overall_winner,
        dimension_averages=dimension_averages,
        judge_summary=judge_summary,
    )
