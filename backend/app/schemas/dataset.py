from datetime import datetime

from app.schemas.base import CamelModel
from app.schemas.rubric import QuestionItem


class QuestionnaireVersionRead(CamelModel):
    """A single versioned snapshot of a questionnaire's questions."""

    id: int
    version_number: int
    questions: list[QuestionItem]
    change_summary: str | None
    created_at: datetime


class QuestionnaireRead(CamelModel):
    """Summary view of a questionnaire without version content."""

    id: int
    name: str
    description: str
    source_material_id: int | None
    current_version: int
    created_at: datetime
    updated_at: datetime


class QuestionnaireReadWithVersions(QuestionnaireRead):
    """QuestionnaireRead with the full version history included."""

    versions: list[QuestionnaireVersionRead]


class QuestionnaireCreate(CamelModel):
    """Payload for creating a new questionnaire."""

    name: str
    description: str
    source_material_id: int | None = None
    questions: list[QuestionItem]


class QuestionnaireUpdate(CamelModel):
    """Payload for adding a new version to an existing questionnaire."""

    questions: list[QuestionItem]
    change_summary: str | None = None
