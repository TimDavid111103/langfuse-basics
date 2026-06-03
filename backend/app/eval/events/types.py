"""Pipeline lifecycle events for experiment evaluation."""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class ExperimentStarted:
    experiment_id: int
    experiment_name: str
    questionnaire_id: int
    source_material_id: int
    num_runs: int


@dataclass(frozen=True, slots=True)
class RunStarted:
    experiment_id: int
    run_index: int


@dataclass(frozen=True, slots=True)
class QuestionEvaluated:
    experiment_id: int
    run_index: int
    question_index: int
    winner: Literal["no_rag", "rag", "tie"]
    no_rag_total: float
    rag_total: float


@dataclass(frozen=True, slots=True)
class RunCompleted:
    experiment_id: int
    run_index: int
    winner: Literal["no_rag", "rag", "tie"]
    no_rag_avg: float
    rag_avg: float


@dataclass(frozen=True, slots=True)
class ExperimentCompleted:
    experiment_id: int
    overall_winner: Literal["no_rag", "rag", "tie"]
    overall_no_rag_score: float
    overall_rag_score: float
    num_runs: int


@dataclass(frozen=True, slots=True)
class ExperimentFailed:
    experiment_id: int
    error: str
