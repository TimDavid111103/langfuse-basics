from datetime import datetime
from enum import StrEnum
from typing import Optional

from sqlalchemy import Column, Text
from sqlmodel import Field, SQLModel


class ExperimentStatus(StrEnum):
    CREATED = "created"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


class Experiment(SQLModel, table=True):
    __tablename__ = "experiment"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    questionnaire_id: int = Field(foreign_key="questionnaire.id", index=True)
    questionnaire_version: int
    source_material_id: int = Field(foreign_key="source_material.id", index=True)
    status: ExperimentStatus = Field(default=ExperimentStatus.CREATED)
    langfuse_trace_id: Optional[str] = Field(default=None)
    error_message: Optional[str] = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)


class ExperimentResult(SQLModel, table=True):
    __tablename__ = "experiment_result"

    id: Optional[int] = Field(default=None, primary_key=True)
    experiment_id: int = Field(foreign_key="experiment.id", index=True)
    run_index: int = Field(default=0)
    question_index: int
    question_text: str = Field(sa_column=Column(Text, nullable=False))
    rubric_no_rag: str = Field(sa_column=Column(Text, nullable=False))
    rubric_rag: str = Field(sa_column=Column(Text, nullable=False))
    retrieved_chunks_json: str = Field(sa_column=Column(Text, nullable=False))
    evaluation_json: Optional[str] = Field(default=None, sa_column=Column(Text))
    winner: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
