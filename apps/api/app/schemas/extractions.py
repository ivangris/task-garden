from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import TaskEffort, TaskEnergy, TaskPriority


CandidateDecision = Literal["accepted", "rejected"]
CandidateStatus = Literal["pending_review", "accepted", "edited", "rejected"]


class ExtractionCandidateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    extraction_batch_id: str
    title: str
    details: str | None = None
    project_or_group: str | None = None
    priority: TaskPriority
    effort: TaskEffort
    energy: TaskEnergy
    labels: list[str]
    due_date: str | None = None
    parent_task_title: str | None = None
    confidence: float
    source_excerpt: str | None = None
    candidate_status: CandidateStatus


class ExtractionBatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    raw_entry_id: str
    provider_name: str
    model_name: str
    schema_version: str
    prompt_version: str
    summary: str | None = None
    needs_review: bool
    open_questions: list[str]
    created_at: datetime
    candidates: list[ExtractionCandidateResponse]


class ConfirmExtractionCandidateRequest(BaseModel):
    id: str
    decision: CandidateDecision
    title: str = Field(min_length=1, max_length=255)
    details: str | None = Field(default=None, max_length=4000)
    project_or_group: str | None = Field(default=None, max_length=255)
    priority: TaskPriority
    effort: TaskEffort
    energy: TaskEnergy
    labels: list[str] = Field(default_factory=list)
    due_date: str | None = None
    parent_task_title: str | None = Field(default=None, max_length=255)
    confidence: float = Field(ge=0.0, le=1.0)
    source_excerpt: str | None = Field(default=None, max_length=1000)

    @field_validator("labels")
    @classmethod
    def normalize_labels(cls, labels: list[str]) -> list[str]:
        return [label.strip() for label in labels if label.strip()]


class ConfirmExtractionRequest(BaseModel):
    candidates: list[ConfirmExtractionCandidateRequest]


class ConfirmExtractionResponse(BaseModel):
    extraction_id: str
    created_task_ids: list[str]
    accepted_count: int
    rejected_count: int
    updated_candidates: list[ExtractionCandidateResponse]


class ProviderExtractionCandidate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    details: str | None = Field(default=None, max_length=4000)
    project_or_group: str | None = Field(default=None, max_length=255)
    priority: TaskPriority = "medium"
    effort: TaskEffort = "medium"
    energy: TaskEnergy = "medium"
    labels: list[str] = Field(default_factory=list)
    due_date: str | None = None
    parent_task_title: str | None = Field(default=None, max_length=255)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source_excerpt: str | None = Field(default=None, max_length=1000)

    @field_validator("labels")
    @classmethod
    def normalize_provider_labels(cls, labels: list[str]) -> list[str]:
        return [label.strip() for label in labels if label.strip()]


class ProviderExtractionEnvelope(BaseModel):
    summary: str | None = Field(default=None, max_length=1000)
    open_questions: list[str] = Field(default_factory=list)
    candidates: list[ProviderExtractionCandidate] = Field(default_factory=list)

    @field_validator("open_questions")
    @classmethod
    def normalize_open_questions(cls, values: list[str]) -> list[str]:
        return [value.strip() for value in values if value.strip()]
