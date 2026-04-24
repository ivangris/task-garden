from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.tasks import TaskResponse


RecommendationLevel = Literal["info", "warning"]
RecommendationRule = Literal[
    "stale_task",
    "overloaded_week",
    "neglected_project",
    "large_task_breakdown",
    "small_wins",
]


class RecommendationReason(BaseModel):
    label: str
    value: str


class RecommendationItemResponse(BaseModel):
    id: str
    rule_type: RecommendationRule
    level: RecommendationLevel
    title: str
    rationale: str
    task_id: str | None = None
    project_id: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)
    reasons: list[RecommendationReason] = Field(default_factory=list)


class RecommendationCurrentResponse(BaseModel):
    snapshot_id: str
    generated_at: datetime
    items: list[RecommendationItemResponse]
    thresholds: dict[str, int]


class WeeklyPreviewResponse(BaseModel):
    snapshot_id: str
    generated_at: datetime
    window_start: datetime
    window_end: datetime
    top_focus_items: list[TaskResponse]
    warnings: list[RecommendationItemResponse]
    suggestion_summaries: list[str]
    thresholds: dict[str, int]
