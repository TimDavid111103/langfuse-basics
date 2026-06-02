from datetime import datetime
from typing import Literal

from app.models.experiment import ExperimentStatus
from app.schemas.base import CamelModel
from app.schemas.evaluation import ExperimentEvaluationSummary


class ExperimentCreate(CamelModel):
    name: str
    questionnaire_id: int
    questionnaire_version: int
    source_material_id: int


class ExperimentRead(CamelModel):
    id: int
    name: str
    questionnaire_id: int
    questionnaire_version: int
    source_material_id: int
    status: ExperimentStatus
    langfuse_trace_id: str | None
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None


class ExperimentResultRead(CamelModel):
    id: int
    experiment_id: int
    run_index: int
    question_index: int
    question_text: str
    rubric_no_rag: str
    rubric_rag: str
    retrieved_chunks_json: str
    evaluation_json: str | None
    winner: Literal["no_rag", "rag", "tie"] | None
    created_at: datetime


class ExperimentRunResponse(CamelModel):
    experiment_id: int
    status: ExperimentStatus
    message: str
