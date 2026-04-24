from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RawEntryModel(Base):
    __tablename__ = "raw_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    audio_file_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    transcript_provider_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    transcript_model_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    transcript_metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    entry_status: Mapped[str] = mapped_column(String(32), nullable=False)
    device_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class TranscriptSegmentModel(Base):
    __tablename__ = "transcript_segments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    raw_entry_id: Mapped[str] = mapped_column(ForeignKey("raw_entries.id"), nullable=False)
    segment_index: Mapped[int] = mapped_column(nullable=False)
    start_ms: Mapped[int | None] = mapped_column(nullable=True)
    end_ms: Mapped[int | None] = mapped_column(nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    speaker_label: Mapped[str | None] = mapped_column(String(64), nullable=True)


class ExtractionBatchModel(Base):
    __tablename__ = "extraction_batches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    raw_entry_id: Mapped[str] = mapped_column(ForeignKey("raw_entries.id"), nullable=False)
    provider_name: Mapped[str] = mapped_column(String(64), nullable=False)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(32), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(32), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    needs_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    open_questions_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class ExtractedTaskCandidateModel(Base):
    __tablename__ = "extracted_task_candidates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    extraction_batch_id: Mapped[str] = mapped_column(ForeignKey("extraction_batches.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    project_or_group: Mapped[str | None] = mapped_column(String(255), nullable=True)
    priority: Mapped[str] = mapped_column(String(16), nullable=False)
    effort: Mapped[str] = mapped_column(String(16), nullable=False)
    energy: Mapped[str] = mapped_column(String(16), nullable=False)
    labels_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_date: Mapped[str | None] = mapped_column(String(32), nullable=True)
    parent_task_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    source_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    candidate_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending_review")


class ProjectModel(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    color_token: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class TaskModel(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    project_id: Mapped[str | None] = mapped_column(ForeignKey("projects.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    priority: Mapped[str] = mapped_column(String(16), nullable=False)
    effort: Mapped[str] = mapped_column(String(16), nullable=False)
    energy: Mapped[str] = mapped_column(String(16), nullable=False)
    source_raw_entry_id: Mapped[str | None] = mapped_column(ForeignKey("raw_entries.id"), nullable=True)
    source_extraction_batch_id: Mapped[str | None] = mapped_column(ForeignKey("extraction_batches.id"), nullable=True)
    parent_task_id: Mapped[str | None] = mapped_column(ForeignKey("tasks.id"), nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    device_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    sync_status: Mapped[str] = mapped_column(String(32), nullable=False, default="local_only")
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class ActivityEventModel(Base):
    __tablename__ = "activity_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    device_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class AppSettingModel(Base):
    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class RecommendationSnapshotModel(Base):
    __tablename__ = "recommendation_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    snapshot_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    window_start: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    window_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class GardenStateModel(Base):
    __tablename__ = "garden_state"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    baseline_key: Mapped[str] = mapped_column(String(64), nullable=False)
    stage_key: Mapped[str] = mapped_column(String(64), nullable=False)
    total_xp: Mapped[int] = mapped_column(nullable=False, default=0)
    current_level: Mapped[int] = mapped_column(nullable=False, default=1)
    total_growth_units: Mapped[int] = mapped_column(nullable=False, default=0)
    total_decay_points: Mapped[int] = mapped_column(nullable=False, default=0)
    active_task_count: Mapped[int] = mapped_column(nullable=False, default=0)
    overdue_task_count: Mapped[int] = mapped_column(nullable=False, default=0)
    restored_tile_count: Mapped[int] = mapped_column(nullable=False, default=0)
    healthy_tile_count: Mapped[int] = mapped_column(nullable=False, default=0)
    lush_tile_count: Mapped[int] = mapped_column(nullable=False, default=0)
    health_score: Mapped[int] = mapped_column(nullable=False, default=0)
    last_recomputed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class GardenZoneModel(Base):
    __tablename__ = "garden_zones"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    zone_key: Mapped[str] = mapped_column(String(64), nullable=False)
    sort_order: Mapped[int] = mapped_column(nullable=False)
    tile_count: Mapped[int] = mapped_column(nullable=False)
    unlocked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class GardenTileModel(Base):
    __tablename__ = "garden_tiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    zone_id: Mapped[str] = mapped_column(ForeignKey("garden_zones.id"), nullable=False)
    tile_index: Mapped[int] = mapped_column(nullable=False)
    coord_x: Mapped[int] = mapped_column(nullable=False)
    coord_y: Mapped[int] = mapped_column(nullable=False)
    tile_state: Mapped[str] = mapped_column(String(32), nullable=False)
    growth_units: Mapped[int] = mapped_column(nullable=False, default=0)
    decay_points: Mapped[int] = mapped_column(nullable=False, default=0)
    last_changed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class PlantInstanceModel(Base):
    __tablename__ = "plant_instances"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    garden_tile_id: Mapped[str] = mapped_column(ForeignKey("garden_tiles.id"), nullable=False)
    plant_key: Mapped[str] = mapped_column(String(64), nullable=False)
    growth_stage: Mapped[str] = mapped_column(String(32), nullable=False)
    unlocked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class DecorationInstanceModel(Base):
    __tablename__ = "decoration_instances"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    garden_tile_id: Mapped[str] = mapped_column(ForeignKey("garden_tiles.id"), nullable=False)
    decoration_key: Mapped[str] = mapped_column(String(64), nullable=False)
    variant_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    unlocked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class XPLedgerEntryModel(Base):
    __tablename__ = "xp_ledger"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"), nullable=False)
    xp_amount: Mapped[int] = mapped_column(nullable=False)
    effort_value: Mapped[int] = mapped_column(nullable=False)
    priority_bonus: Mapped[int] = mapped_column(nullable=False)
    streak_multiplier: Mapped[float] = mapped_column(Float, nullable=False)
    awarded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class UnlockLedgerEntryModel(Base):
    __tablename__ = "unlock_ledger"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    unlock_key: Mapped[str] = mapped_column(String(64), nullable=False)
    unlock_type: Mapped[str] = mapped_column(String(32), nullable=False)
    threshold_value: Mapped[int] = mapped_column(nullable=False)
    unlocked_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class DecayEventModel(Base):
    __tablename__ = "decay_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"), nullable=False)
    task_title: Mapped[str] = mapped_column(String(255), nullable=False)
    days_overdue: Mapped[int] = mapped_column(nullable=False)
    decay_points: Mapped[int] = mapped_column(nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class RecoveryEventModel(Base):
    __tablename__ = "recovery_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"), nullable=False)
    task_title: Mapped[str] = mapped_column(String(255), nullable=False)
    recovery_points: Mapped[int] = mapped_column(nullable=False)
    xp_amount: Mapped[int] = mapped_column(nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class RecapPeriodModel(Base):
    __tablename__ = "recap_periods"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    period_type: Mapped[str] = mapped_column(String(16), nullable=False)
    period_label: Mapped[str] = mapped_column(String(128), nullable=False)
    window_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    window_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class RecapMetricSnapshotModel(Base):
    __tablename__ = "recap_metric_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    period_id: Mapped[str] = mapped_column(ForeignKey("recap_periods.id"), nullable=False)
    metric_key: Mapped[str] = mapped_column(String(64), nullable=False)
    sort_order: Mapped[int] = mapped_column(nullable=False, default=0)
    numeric_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    text_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    json_value_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class HighlightCardModel(Base):
    __tablename__ = "highlight_cards"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    period_id: Mapped[str] = mapped_column(ForeignKey("recap_periods.id"), nullable=False)
    card_type: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    subtitle: Mapped[str | None] = mapped_column(String(255), nullable=True)
    primary_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    secondary_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    supporting_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    visual_hint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    sort_order: Mapped[int] = mapped_column(nullable=False, default=0)


class MilestoneModel(Base):
    __tablename__ = "milestones"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    period_id: Mapped[str] = mapped_column(ForeignKey("recap_periods.id"), nullable=False)
    milestone_key: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    metric_value: Mapped[int | None] = mapped_column(nullable=True)
    detected_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sort_order: Mapped[int] = mapped_column(nullable=False, default=0)


class StreakSummaryModel(Base):
    __tablename__ = "streak_summaries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    period_id: Mapped[str] = mapped_column(ForeignKey("recap_periods.id"), nullable=False, unique=True)
    current_streak_days: Mapped[int] = mapped_column(nullable=False, default=0)
    longest_streak_days: Mapped[int] = mapped_column(nullable=False, default=0)
    period_best_streak_days: Mapped[int] = mapped_column(nullable=False, default=0)
    active_days: Mapped[int] = mapped_column(nullable=False, default=0)
    streak_start: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    streak_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class ProjectSummaryModel(Base):
    __tablename__ = "project_summaries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    period_id: Mapped[str] = mapped_column(ForeignKey("recap_periods.id"), nullable=False)
    project_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    project_name: Mapped[str] = mapped_column(String(255), nullable=False)
    completed_task_count: Mapped[int] = mapped_column(nullable=False, default=0)
    xp_gained: Mapped[int] = mapped_column(nullable=False, default=0)
    completion_share: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    effort_small_count: Mapped[int] = mapped_column(nullable=False, default=0)
    effort_medium_count: Mapped[int] = mapped_column(nullable=False, default=0)
    effort_large_count: Mapped[int] = mapped_column(nullable=False, default=0)
    latest_completion_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sort_order: Mapped[int] = mapped_column(nullable=False, default=0)


class RecapNarrativeModel(Base):
    __tablename__ = "recap_narratives"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    period_id: Mapped[str] = mapped_column(ForeignKey("recap_periods.id"), nullable=False, unique=True)
    generation_status: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_name: Mapped[str] = mapped_column(String(64), nullable=False)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(32), nullable=False)
    source_summary_version: Mapped[str] = mapped_column(String(32), nullable=False)
    source_summary_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    narrative_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class DeviceModel(Base):
    __tablename__ = "devices"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    device_name: Mapped[str] = mapped_column(String(255), nullable=False)
    platform: Mapped[str] = mapped_column(String(128), nullable=False)
    app_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    registered_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ChangeEventModel(Base):
    __tablename__ = "change_events"

    sequence: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(128), nullable=False)
    change_type: Mapped[str] = mapped_column(String(64), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    device_id: Mapped[str | None] = mapped_column(ForeignKey("devices.id"), nullable=True)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)


class SyncCursorModel(Base):
    __tablename__ = "sync_cursors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    device_id: Mapped[str] = mapped_column(ForeignKey("devices.id"), nullable=False)
    stream_key: Mapped[str] = mapped_column(String(64), nullable=False)
    cursor_value: Mapped[int] = mapped_column(nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
