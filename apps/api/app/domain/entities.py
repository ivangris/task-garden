from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class RawEntry:
    id: str
    source_type: str
    raw_text: str
    entry_status: str
    created_at: datetime
    updated_at: datetime
    device_id: str | None = None
    audio_file_ref: str | None = None
    transcript_provider_name: str | None = None
    transcript_model_name: str | None = None
    transcript_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class TranscriptSegment:
    id: str
    raw_entry_id: str
    segment_index: int
    text: str
    start_ms: int | None = None
    end_ms: int | None = None
    speaker_label: str | None = None


@dataclass(slots=True)
class ExtractionBatch:
    id: str
    raw_entry_id: str
    provider_name: str
    model_name: str
    schema_version: str
    prompt_version: str
    summary: str | None
    needs_review: bool
    open_questions: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(slots=True)
class ExtractedTaskCandidate:
    id: str
    extraction_batch_id: str
    title: str
    priority: str
    effort: str
    energy: str
    candidate_status: str
    details: str | None = None
    project_or_group: str | None = None
    labels: list[str] = field(default_factory=list)
    due_date: str | None = None
    parent_task_title: str | None = None
    confidence: float = 0.0
    source_excerpt: str | None = None


@dataclass(slots=True)
class Task:
    id: str
    title: str
    status: str
    priority: str
    effort: str
    energy: str
    created_at: datetime
    updated_at: datetime
    details: str | None = None
    project_id: str | None = None
    due_date: datetime | None = None
    completed_at: datetime | None = None
    parent_task_id: str | None = None
    source_raw_entry_id: str | None = None
    source_extraction_batch_id: str | None = None
    device_id: str | None = None
    sync_status: str = "local_only"
    is_deleted: bool = False


@dataclass(slots=True)
class Project:
    id: str
    name: str
    created_at: datetime
    updated_at: datetime
    description: str | None = None
    color_token: str | None = None
    is_archived: bool = False


@dataclass(slots=True)
class ActivityEvent:
    id: str
    event_type: str
    entity_type: str
    entity_id: str
    metadata: dict[str, Any]
    created_at: datetime
    device_id: str | None = None


@dataclass(slots=True)
class RecommendationSnapshot:
    id: str
    snapshot_kind: str
    generated_at: datetime
    payload: dict[str, Any]
    window_start: datetime | None = None
    window_end: datetime | None = None


@dataclass(slots=True)
class GardenState:
    id: str
    baseline_key: str
    stage_key: str
    total_xp: int
    current_level: int
    total_growth_units: int
    total_decay_points: int
    active_task_count: int
    overdue_task_count: int
    restored_tile_count: int
    healthy_tile_count: int
    lush_tile_count: int
    health_score: int
    last_recomputed_at: datetime


@dataclass(slots=True)
class GardenZone:
    id: str
    name: str
    zone_key: str
    sort_order: int
    tile_count: int
    unlocked_at: datetime | None = None


@dataclass(slots=True)
class GardenTile:
    id: str
    zone_id: str
    tile_index: int
    coord_x: int
    coord_y: int
    tile_state: str
    growth_units: int
    decay_points: int
    last_changed_at: datetime


@dataclass(slots=True)
class PlantInstance:
    id: str
    garden_tile_id: str
    plant_key: str
    growth_stage: str
    unlocked_at: datetime | None = None


@dataclass(slots=True)
class DecorationInstance:
    id: str
    garden_tile_id: str
    decoration_key: str
    variant_key: str | None = None
    unlocked_at: datetime | None = None


@dataclass(slots=True)
class XPLedgerEntry:
    id: str
    task_id: str
    xp_amount: int
    effort_value: int
    priority_bonus: int
    streak_multiplier: float
    awarded_at: datetime


@dataclass(slots=True)
class UnlockLedgerEntry:
    id: str
    unlock_key: str
    unlock_type: str
    threshold_value: int
    unlocked_at: datetime


@dataclass(slots=True)
class DecayEvent:
    id: str
    task_id: str
    task_title: str
    days_overdue: int
    decay_points: int
    recorded_at: datetime


@dataclass(slots=True)
class RecoveryEvent:
    id: str
    task_id: str
    task_title: str
    recovery_points: int
    xp_amount: int
    recorded_at: datetime


@dataclass(slots=True)
class RecapPeriod:
    id: str
    period_type: str
    period_label: str
    window_start: datetime
    window_end: datetime
    generated_at: datetime


@dataclass(slots=True)
class RecapMetricSnapshot:
    id: str
    period_id: str
    metric_key: str
    sort_order: int
    numeric_value: float | None = None
    text_value: str | None = None
    json_value: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class HighlightCard:
    id: str
    period_id: str
    card_type: str
    title: str
    sort_order: int
    subtitle: str | None = None
    primary_value: str | None = None
    secondary_value: str | None = None
    supporting_text: str | None = None
    visual_hint: str | None = None


@dataclass(slots=True)
class Milestone:
    id: str
    period_id: str
    milestone_key: str
    title: str
    description: str
    sort_order: int
    metric_value: int | None = None
    detected_at: datetime | None = None


@dataclass(slots=True)
class StreakSummary:
    id: str
    period_id: str
    current_streak_days: int
    longest_streak_days: int
    period_best_streak_days: int
    active_days: int
    streak_start: datetime | None = None
    streak_end: datetime | None = None


@dataclass(slots=True)
class ProjectSummary:
    id: str
    period_id: str
    project_name: str
    completed_task_count: int
    xp_gained: int
    sort_order: int
    project_id: str | None = None
    completion_share: float = 0.0
    effort_small_count: int = 0
    effort_medium_count: int = 0
    effort_large_count: int = 0
    latest_completion_at: datetime | None = None


@dataclass(slots=True)
class RecapNarrative:
    id: str
    period_id: str
    generation_status: str
    provider_name: str
    model_name: str
    prompt_version: str
    source_summary_version: str
    source_summary_hash: str
    generated_at: datetime
    narrative_text: str | None = None
    error_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Device:
    id: str
    device_name: str
    platform: str
    app_version: str | None
    registered_at: datetime
    last_seen_at: datetime
    last_sync_at: datetime | None = None
    is_active: bool = True


@dataclass(slots=True)
class ChangeEvent:
    sequence: int
    event_id: str
    entity_type: str
    entity_id: str
    change_type: str
    changed_at: datetime
    payload: dict[str, Any]
    device_id: str | None = None


@dataclass(slots=True)
class SyncCursor:
    id: str
    device_id: str
    stream_key: str
    cursor_value: int
    updated_at: datetime
