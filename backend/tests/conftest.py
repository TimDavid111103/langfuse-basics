"""Shared test fixtures."""

import pytest

from app.judging.aggregation import EVAL_DIMENSIONS
from app.judging.schemas import DimensionScore, QuestionEvaluationResult


def make_dimension_scores(
    *,
    no_rag: float = 7.0,
    rag: float = 8.0,
) -> list[DimensionScore]:
    return [
        DimensionScore(
            dimension=dim,  # type: ignore[arg-type]
            rubric_no_rag_score=no_rag,
            rubric_rag_score=rag,
            reasoning=f"{dim} reasoning",
        )
        for dim in EVAL_DIMENSIONS
    ]


def make_question_result(
    *,
    run_index: int = 0,
    question_index: int = 0,
    no_rag_total: float = 28.0,
    rag_total: float = 32.0,
    winner: str = "rag",
) -> QuestionEvaluationResult:
    return QuestionEvaluationResult(
        run_index=run_index,
        question_index=question_index,
        question_text=f"Question {question_index}",
        dimension_scores=make_dimension_scores(
            no_rag=no_rag_total / len(EVAL_DIMENSIONS),
            rag=rag_total / len(EVAL_DIMENSIONS),
        ),
        no_rag_total=no_rag_total,
        rag_total=rag_total,
        winner=winner,  # type: ignore[arg-type]
        judge_reasoning="test reasoning",
        judge_model="gpt-4o-mini",
    )


@pytest.fixture
def sample_question_result() -> QuestionEvaluationResult:
    return make_question_result()


@pytest.fixture
def sample_runs() -> list[list[QuestionEvaluationResult]]:
    """Two runs with two questions each; RAG wins overall."""
    return [
        [
            make_question_result(run_index=0, question_index=0, no_rag_total=26.0, rag_total=30.0),
            make_question_result(run_index=0, question_index=1, no_rag_total=28.0, rag_total=32.0),
        ],
        [
            make_question_result(run_index=1, question_index=0, no_rag_total=24.0, rag_total=28.0),
            make_question_result(run_index=1, question_index=1, no_rag_total=30.0, rag_total=34.0),
        ],
    ]
