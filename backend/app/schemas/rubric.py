from typing import Literal

from app.schemas.base import CamelModel


class QuestionItem(CamelModel):
    """A single question used as input for rubric generation."""

    index: int
    text: str


class RubricCriterion(CamelModel):
    """A single scorable criterion within a generated rubric."""

    criterion_name: str
    description: str
    point_value: int
    example_correct_response: str
    example_incorrect_response: str
    physics_concepts_required: list[str]


class GeneratedRubric(CamelModel):
    """A fully generated rubric for one question under one condition (rag or no_rag)."""

    question_index: int
    question_text: str
    criteria: list[RubricCriterion]
    total_points: int
    condition: Literal["no_rag", "rag"]
    model_id: str
    prompt_tokens: int
    completion_tokens: int


class RubricGenerateNoRagRequest(CamelModel):
    """Request body for no-RAG rubric generation."""

    questions: list[QuestionItem]


class RubricGenerateRagRequest(CamelModel):
    """Request body for RAG rubric generation."""

    questions: list[QuestionItem]
    source_material_id: int
    top_k: int = 5
