"""Evaluation package: judge, aggregation, schemas, and pipeline events."""

from app.eval.aggregation import aggregate_results, run_winner
from app.eval.judge import evaluate_rubrics
from app.eval.schemas import (
    DimensionScore,
    ExperimentEvaluationSummary,
    QuestionEvaluationResult,
    RunSummary,
)

__all__ = [
    "DimensionScore",
    "ExperimentEvaluationSummary",
    "QuestionEvaluationResult",
    "RunSummary",
    "aggregate_results",
    "evaluate_rubrics",
    "run_winner",
]
