from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Text
from sqlmodel import Field, SQLModel


class Questionnaire(SQLModel, table=True):
    """A named set of exam questions, versioned over time."""

    __tablename__ = "questionnaire"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: str
    # Optional link to the source material the questions are drawn from.
    source_material_id: Optional[int] = Field(
        default=None, foreign_key="source_material.id", index=True
    )
    current_version: int = Field(default=1)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class QuestionnaireVersion(SQLModel, table=True):
    """An immutable snapshot of a questionnaire's questions at a given version."""

    __tablename__ = "questionnaire_version"

    id: Optional[int] = Field(default=None, primary_key=True)
    questionnaire_id: int = Field(foreign_key="questionnaire.id", index=True)
    version_number: int
    # JSON-serialised list of QuestionItem dicts.
    questions_json: str = Field(sa_column=Column(Text, nullable=False))
    change_summary: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
