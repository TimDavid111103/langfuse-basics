from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Text
from sqlmodel import Field, SQLModel


class Questionnaire(SQLModel, table=True):
    __tablename__ = "questionnaire"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: str
    source_material_id: Optional[int] = Field(
        default=None, foreign_key="source_material.id", index=True
    )
    current_version: int = Field(default=1)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class QuestionnaireVersion(SQLModel, table=True):
    __tablename__ = "questionnaire_version"

    id: Optional[int] = Field(default=None, primary_key=True)
    questionnaire_id: int = Field(foreign_key="questionnaire.id", index=True)
    version_number: int
    questions_json: str = Field(sa_column=Column(Text, nullable=False))
    change_summary: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
