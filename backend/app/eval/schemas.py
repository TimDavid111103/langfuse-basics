from typing import Literal

from pydantic import Field

from app.schemas.base import CamelModel


class DimensionScore(CamelModel):
    """Judge score for a single evaluation dimension, comparing both rubric conditions."""

    dimension: Literal[
        "concept_coverage",
        "factual_accuracy",
        "specificity",
        "subject_matter_depth",
    ]
    rubric_no_rag_score: float = Field(ge=0.0, le=10.0)
    rubric_rag_score: float = Field(ge=0.0, le=10.0)
    reasoning: str


class QuestionEvaluationResult(CamelModel):
    """All judge outputs for a single question within a single run."""

    run_index: int
    question_index: int
    question_text: str
    dimension_scores: list[DimensionScore]
    no_rag_total: float
    rag_total: float
    winner: Literal["no_rag", "rag", "tie"]
    judge_reasoning: str
    judge_model: str


class RunSummary(CamelModel):
    """Aggregate outcome across all questions for a single run."""

    run_index: int
    per_question_results: list[QuestionEvaluationResult]
    no_rag_avg: float
    rag_avg: float
    winner: Literal["no_rag", "rag", "tie"]


class ExperimentEvaluationSummary(CamelModel):
    """Top-level summary aggregated across all runs of an experiment."""

    experiment_id: int
    num_runs: int
    runs: list[RunSummary]
    overall_no_rag_score: float
    overall_rag_score: float
    overall_winner: Literal["no_rag", "rag", "tie"]
    dimension_averages: dict[str, dict[Literal["no_rag", "rag"], float]]
    judge_summary: str
