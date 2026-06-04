"""Evaluation package: judge, aggregation, schemas, and pipeline events."""

from app.judging.aggregation import aggregate_results, run_winner
from app.judging.judge import evaluate_rubrics
from app.judging.schemas import (
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
