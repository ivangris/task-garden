from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


PeriodType = Literal["weekly", "monthly", "yearly"]


class RecapMetricValueResponse(BaseModel):
    metric_key: str
    numeric_value: float | None = None
    text_value: str | None = None
    json_value: dict[str, Any] = Field(default_factory=dict)


class HighlightCardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    period_id: str
    card_type: str
    title: str
    subtitle: str | None = None
    primary_value: str | None = None
    secondary_value: str | None = None
    supporting_text: str | None = None
    visual_hint: str | None = None
    sort_order: int


class MilestoneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    period_id: str
    milestone_key: str
    title: str
    description: str
    sort_order: int
    metric_value: int | None = None
    detected_at: datetime | None = None


class StreakSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    period_id: str
    current_streak_days: int
    longest_streak_days: int
    period_best_streak_days: int
    active_days: int
    streak_start: datetime | None = None
    streak_end: datetime | None = None


class ProjectSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    period_id: str
    project_id: str | None = None
    project_name: str
    completed_task_count: int
    xp_gained: int
    completion_share: float
    effort_small_count: int
    effort_medium_count: int
    effort_large_count: int
    latest_completion_at: datetime | None = None
    sort_order: int


class RecapNarrativeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str | None = None
    period_id: str
    generation_status: str
    provider_name: str | None = None
    model_name: str | None = None
    prompt_version: str | None = None
    source_summary_version: str | None = None
    source_summary_hash: str | None = None
    narrative_text: str | None = None
    error_metadata: dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime | None = None


class RecapPeriodResponse(BaseModel):
    id: str
    period_type: PeriodType
    period_label: str
    window_start: datetime
    window_end: datetime
    generated_at: datetime
    metrics: list[RecapMetricValueResponse]
    cards: list[HighlightCardResponse]
    milestones: list[MilestoneResponse]
    streak_summary: StreakSummaryResponse | None = None
    project_summaries: list[ProjectSummaryResponse]
    narrative: RecapNarrativeResponse | None = None


class HighlightCardListResponse(BaseModel):
    items: list[HighlightCardResponse]
