import json
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    ActivityEventModel,
    AppSettingModel,
    ChangeEventModel,
    DecayEventModel,
    DeviceModel,
    DecorationInstanceModel,
    ExtractedTaskCandidateModel,
    ExtractionBatchModel,
    GardenStateModel,
    GardenTileModel,
    GardenZoneModel,
    HighlightCardModel,
    MilestoneModel,
    PlantInstanceModel,
    ProjectSummaryModel,
    ProjectModel,
    RawEntryModel,
    RecapMetricSnapshotModel,
    RecapNarrativeModel,
    RecapPeriodModel,
    RecoveryEventModel,
    RecommendationSnapshotModel,
    StreakSummaryModel,
    SyncCursorModel,
    TaskModel,
    TranscriptSegmentModel,
    UnlockLedgerEntryModel,
    XPLedgerEntryModel,
)
from app.domain.entities import (
    ActivityEvent,
    ChangeEvent,
    DecayEvent,
    Device,
    DecorationInstance,
    ExtractedTaskCandidate,
    ExtractionBatch,
    GardenState,
    GardenTile,
    GardenZone,
    HighlightCard,
    Milestone,
    PlantInstance,
    ProjectSummary,
    Project,
    RawEntry,
    RecapMetricSnapshot,
    RecapNarrative,
    RecapPeriod,
    RecommendationSnapshot,
    RecoveryEvent,
    StreakSummary,
    SyncCursor,
    Task,
    TranscriptSegment,
    UnlockLedgerEntry,
    XPLedgerEntry,
)
from app.services.common import utcnow


def _raw_entry_from_model(model: RawEntryModel) -> RawEntry:
    return RawEntry(
        id=model.id,
        source_type=model.source_type,
        raw_text=model.raw_text,
        entry_status=model.entry_status,
        created_at=model.created_at,
        updated_at=model.updated_at,
        device_id=model.device_id,
        audio_file_ref=model.audio_file_ref,
        transcript_provider_name=model.transcript_provider_name,
        transcript_model_name=model.transcript_model_name,
        transcript_metadata=json.loads(model.transcript_metadata_json) if model.transcript_metadata_json else {},
    )


def _segment_from_model(model: TranscriptSegmentModel) -> TranscriptSegment:
    return TranscriptSegment(
        id=model.id,
        raw_entry_id=model.raw_entry_id,
        segment_index=model.segment_index,
        start_ms=model.start_ms,
        end_ms=model.end_ms,
        text=model.text,
        speaker_label=model.speaker_label,
    )


def _task_from_model(model: TaskModel) -> Task:
    return Task(
        id=model.id,
        title=model.title,
        details=model.details,
        project_id=model.project_id,
        status=model.status,
        priority=model.priority,
        effort=model.effort,
        energy=model.energy,
        source_raw_entry_id=model.source_raw_entry_id,
        source_extraction_batch_id=model.source_extraction_batch_id,
        created_at=model.created_at,
        updated_at=model.updated_at,
        due_date=model.due_date,
        completed_at=model.completed_at,
        parent_task_id=model.parent_task_id,
        device_id=model.device_id,
        sync_status=model.sync_status,
        is_deleted=model.is_deleted,
    )


def _extraction_batch_from_model(model: ExtractionBatchModel) -> ExtractionBatch:
    open_questions = json.loads(model.open_questions_json) if model.open_questions_json else []
    return ExtractionBatch(
        id=model.id,
        raw_entry_id=model.raw_entry_id,
        provider_name=model.provider_name,
        model_name=model.model_name,
        schema_version=model.schema_version,
        prompt_version=model.prompt_version,
        summary=model.summary,
        needs_review=model.needs_review,
        open_questions=open_questions,
        created_at=model.created_at,
    )


def _candidate_from_model(model: ExtractedTaskCandidateModel) -> ExtractedTaskCandidate:
    labels = json.loads(model.labels_json) if model.labels_json else []
    return ExtractedTaskCandidate(
        id=model.id,
        extraction_batch_id=model.extraction_batch_id,
        title=model.title,
        details=model.details,
        project_or_group=model.project_or_group,
        priority=model.priority,
        effort=model.effort,
        energy=model.energy,
        labels=labels,
        due_date=model.due_date,
        parent_task_title=model.parent_task_title,
        confidence=model.confidence,
        source_excerpt=model.source_excerpt,
        candidate_status=model.candidate_status,
    )


def _project_from_model(model: ProjectModel) -> Project:
    return Project(
        id=model.id,
        name=model.name,
        description=model.description,
        color_token=model.color_token,
        created_at=model.created_at,
        updated_at=model.updated_at,
        is_archived=model.is_archived,
    )


def _activity_from_model(model: ActivityEventModel) -> ActivityEvent:
    metadata = json.loads(model.metadata_json) if model.metadata_json else {}
    return ActivityEvent(
        id=model.id,
        event_type=model.event_type,
        entity_type=model.entity_type,
        entity_id=model.entity_id,
        metadata=metadata,
        created_at=model.created_at,
        device_id=model.device_id,
    )


def _device_from_model(model: DeviceModel) -> Device:
    return Device(
        id=model.id,
        device_name=model.device_name,
        platform=model.platform,
        app_version=model.app_version,
        registered_at=model.registered_at,
        last_seen_at=model.last_seen_at,
        last_sync_at=model.last_sync_at,
        is_active=model.is_active,
    )


def _change_event_from_model(model: ChangeEventModel) -> ChangeEvent:
    return ChangeEvent(
        sequence=model.sequence,
        event_id=model.event_id,
        entity_type=model.entity_type,
        entity_id=model.entity_id,
        change_type=model.change_type,
        changed_at=model.changed_at,
        device_id=model.device_id,
        payload=json.loads(model.payload_json) if model.payload_json else {},
    )


def _sync_cursor_from_model(model: SyncCursorModel) -> SyncCursor:
    return SyncCursor(
        id=model.id,
        device_id=model.device_id,
        stream_key=model.stream_key,
        cursor_value=model.cursor_value,
        updated_at=model.updated_at,
    )


def _recommendation_snapshot_from_model(model: RecommendationSnapshotModel) -> RecommendationSnapshot:
    payload = json.loads(model.payload_json) if model.payload_json else {}
    return RecommendationSnapshot(
        id=model.id,
        snapshot_kind=model.snapshot_kind,
        payload=payload,
        window_start=model.window_start,
        window_end=model.window_end,
        generated_at=model.generated_at,
    )


def _garden_state_from_model(model: GardenStateModel) -> GardenState:
    return GardenState(
        id=model.id,
        baseline_key=model.baseline_key,
        stage_key=model.stage_key,
        total_xp=model.total_xp,
        current_level=model.current_level,
        total_growth_units=model.total_growth_units,
        total_decay_points=model.total_decay_points,
        active_task_count=model.active_task_count,
        overdue_task_count=model.overdue_task_count,
        restored_tile_count=model.restored_tile_count,
        healthy_tile_count=model.healthy_tile_count,
        lush_tile_count=model.lush_tile_count,
        health_score=model.health_score,
        last_recomputed_at=model.last_recomputed_at,
    )


def _garden_zone_from_model(model: GardenZoneModel) -> GardenZone:
    return GardenZone(
        id=model.id,
        name=model.name,
        zone_key=model.zone_key,
        sort_order=model.sort_order,
        tile_count=model.tile_count,
        unlocked_at=model.unlocked_at,
    )


def _garden_tile_from_model(model: GardenTileModel) -> GardenTile:
    return GardenTile(
        id=model.id,
        zone_id=model.zone_id,
        tile_index=model.tile_index,
        coord_x=model.coord_x,
        coord_y=model.coord_y,
        tile_state=model.tile_state,
        growth_units=model.growth_units,
        decay_points=model.decay_points,
        last_changed_at=model.last_changed_at,
    )


def _plant_instance_from_model(model: PlantInstanceModel) -> PlantInstance:
    return PlantInstance(
        id=model.id,
        garden_tile_id=model.garden_tile_id,
        plant_key=model.plant_key,
        growth_stage=model.growth_stage,
        unlocked_at=model.unlocked_at,
    )


def _decoration_instance_from_model(model: DecorationInstanceModel) -> DecorationInstance:
    return DecorationInstance(
        id=model.id,
        garden_tile_id=model.garden_tile_id,
        decoration_key=model.decoration_key,
        variant_key=model.variant_key,
        unlocked_at=model.unlocked_at,
    )


def _xp_ledger_from_model(model: XPLedgerEntryModel) -> XPLedgerEntry:
    return XPLedgerEntry(
        id=model.id,
        task_id=model.task_id,
        xp_amount=model.xp_amount,
        effort_value=model.effort_value,
        priority_bonus=model.priority_bonus,
        streak_multiplier=model.streak_multiplier,
        awarded_at=model.awarded_at,
    )


def _unlock_ledger_from_model(model: UnlockLedgerEntryModel) -> UnlockLedgerEntry:
    return UnlockLedgerEntry(
        id=model.id,
        unlock_key=model.unlock_key,
        unlock_type=model.unlock_type,
        threshold_value=model.threshold_value,
        unlocked_at=model.unlocked_at,
    )


def _decay_event_from_model(model: DecayEventModel) -> DecayEvent:
    return DecayEvent(
        id=model.id,
        task_id=model.task_id,
        task_title=model.task_title,
        days_overdue=model.days_overdue,
        decay_points=model.decay_points,
        recorded_at=model.recorded_at,
    )


def _recovery_event_from_model(model: RecoveryEventModel) -> RecoveryEvent:
    return RecoveryEvent(
        id=model.id,
        task_id=model.task_id,
        task_title=model.task_title,
        recovery_points=model.recovery_points,
        xp_amount=model.xp_amount,
        recorded_at=model.recorded_at,
    )


def _recap_period_from_model(model: RecapPeriodModel) -> RecapPeriod:
    return RecapPeriod(
        id=model.id,
        period_type=model.period_type,
        period_label=model.period_label,
        window_start=model.window_start,
        window_end=model.window_end,
        generated_at=model.generated_at,
    )


def _recap_metric_from_model(model: RecapMetricSnapshotModel) -> RecapMetricSnapshot:
    return RecapMetricSnapshot(
        id=model.id,
        period_id=model.period_id,
        metric_key=model.metric_key,
        sort_order=model.sort_order,
        numeric_value=model.numeric_value,
        text_value=model.text_value,
        json_value=json.loads(model.json_value_json) if model.json_value_json else {},
    )


def _highlight_card_from_model(model: HighlightCardModel) -> HighlightCard:
    return HighlightCard(
        id=model.id,
        period_id=model.period_id,
        card_type=model.card_type,
        title=model.title,
        subtitle=model.subtitle,
        primary_value=model.primary_value,
        secondary_value=model.secondary_value,
        supporting_text=model.supporting_text,
        visual_hint=model.visual_hint,
        sort_order=model.sort_order,
    )


def _milestone_from_model(model: MilestoneModel) -> Milestone:
    return Milestone(
        id=model.id,
        period_id=model.period_id,
        milestone_key=model.milestone_key,
        title=model.title,
        description=model.description,
        metric_value=model.metric_value,
        detected_at=model.detected_at,
        sort_order=model.sort_order,
    )


def _streak_summary_from_model(model: StreakSummaryModel) -> StreakSummary:
    return StreakSummary(
        id=model.id,
        period_id=model.period_id,
        current_streak_days=model.current_streak_days,
        longest_streak_days=model.longest_streak_days,
        period_best_streak_days=model.period_best_streak_days,
        active_days=model.active_days,
        streak_start=model.streak_start,
        streak_end=model.streak_end,
    )


def _project_summary_from_model(model: ProjectSummaryModel) -> ProjectSummary:
    return ProjectSummary(
        id=model.id,
        period_id=model.period_id,
        project_id=model.project_id,
        project_name=model.project_name,
        completed_task_count=model.completed_task_count,
        xp_gained=model.xp_gained,
        completion_share=model.completion_share,
        effort_small_count=model.effort_small_count,
        effort_medium_count=model.effort_medium_count,
        effort_large_count=model.effort_large_count,
        latest_completion_at=model.latest_completion_at,
        sort_order=model.sort_order,
    )


def _recap_narrative_from_model(model: RecapNarrativeModel) -> RecapNarrative:
    return RecapNarrative(
        id=model.id,
        period_id=model.period_id,
        generation_status=model.generation_status,
        provider_name=model.provider_name,
        model_name=model.model_name,
        prompt_version=model.prompt_version,
        source_summary_version=model.source_summary_version,
        source_summary_hash=model.source_summary_hash,
        generated_at=model.generated_at,
        narrative_text=model.narrative_text,
        error_metadata=json.loads(model.error_metadata_json) if model.error_metadata_json else {},
    )


class SqlAlchemyRawEntryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, entry: RawEntry) -> RawEntry:
        model = RawEntryModel(
            id=entry.id,
            source_type=entry.source_type,
            raw_text=entry.raw_text,
            audio_file_ref=entry.audio_file_ref,
            transcript_provider_name=entry.transcript_provider_name,
            transcript_model_name=entry.transcript_model_name,
            transcript_metadata_json=json.dumps(entry.transcript_metadata),
            entry_status=entry.entry_status,
            device_id=entry.device_id,
            created_at=entry.created_at,
            updated_at=entry.updated_at,
        )
        self.session.add(model)
        self.session.flush()
        return _raw_entry_from_model(model)

    def get(self, entry_id: str) -> RawEntry | None:
        model = self.session.get(RawEntryModel, entry_id)
        return _raw_entry_from_model(model) if model else None

    def list_all(self) -> list[RawEntry]:
        models = self.session.scalars(
            select(RawEntryModel)
            .where(RawEntryModel.entry_status != "archived")
            .order_by(RawEntryModel.created_at.desc())
        ).all()
        return [_raw_entry_from_model(model) for model in models]

    def update(self, entry: RawEntry) -> RawEntry:
        model = self.session.get(RawEntryModel, entry.id)
        if model is None:
            raise ValueError(f"Raw entry {entry.id} not found")
        model.source_type = entry.source_type
        model.raw_text = entry.raw_text
        model.audio_file_ref = entry.audio_file_ref
        model.transcript_provider_name = entry.transcript_provider_name
        model.transcript_model_name = entry.transcript_model_name
        model.transcript_metadata_json = json.dumps(entry.transcript_metadata)
        model.entry_status = entry.entry_status
        model.device_id = entry.device_id
        model.created_at = entry.created_at
        model.updated_at = entry.updated_at
        self.session.flush()
        return _raw_entry_from_model(model)

    def archive(self, entry_id: str) -> RawEntry | None:
        model = self.session.get(RawEntryModel, entry_id)
        if model is None:
            return None
        model.entry_status = "archived"
        model.updated_at = utcnow()
        self.session.flush()
        return _raw_entry_from_model(model)


class SqlAlchemyTranscriptSegmentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_for_entry(self, raw_entry_id: str) -> list[TranscriptSegment]:
        models = self.session.scalars(
            select(TranscriptSegmentModel)
            .where(TranscriptSegmentModel.raw_entry_id == raw_entry_id)
            .order_by(TranscriptSegmentModel.segment_index.asc())
        ).all()
        return [_segment_from_model(model) for model in models]

    def replace_for_entry(self, raw_entry_id: str, segments: list[TranscriptSegment]) -> list[TranscriptSegment]:
        existing = self.session.scalars(
            select(TranscriptSegmentModel).where(TranscriptSegmentModel.raw_entry_id == raw_entry_id)
        ).all()
        for model in existing:
            self.session.delete(model)
        created: list[TranscriptSegmentModel] = []
        for segment in segments:
            model = TranscriptSegmentModel(
                id=segment.id,
                raw_entry_id=segment.raw_entry_id,
                segment_index=segment.segment_index,
                start_ms=segment.start_ms,
                end_ms=segment.end_ms,
                text=segment.text,
                speaker_label=segment.speaker_label,
            )
            self.session.add(model)
            created.append(model)
        self.session.flush()
        return [_segment_from_model(model) for model in created]


class SqlAlchemyExtractionBatchRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, batch: ExtractionBatch) -> ExtractionBatch:
        model = ExtractionBatchModel(
            id=batch.id,
            raw_entry_id=batch.raw_entry_id,
            provider_name=batch.provider_name,
            model_name=batch.model_name,
            schema_version=batch.schema_version,
            prompt_version=batch.prompt_version,
            summary=batch.summary,
            needs_review=batch.needs_review,
            open_questions_json=json.dumps(batch.open_questions),
            created_at=batch.created_at,
        )
        self.session.add(model)
        self.session.flush()
        return _extraction_batch_from_model(model)

    def get(self, extraction_batch_id: str) -> ExtractionBatch | None:
        model = self.session.get(ExtractionBatchModel, extraction_batch_id)
        return _extraction_batch_from_model(model) if model else None

    def list_for_entry(self, raw_entry_id: str) -> list[ExtractionBatch]:
        models = self.session.scalars(
            select(ExtractionBatchModel)
            .where(ExtractionBatchModel.raw_entry_id == raw_entry_id)
            .order_by(ExtractionBatchModel.created_at.desc())
        ).all()
        return [_extraction_batch_from_model(model) for model in models]

    def update(self, batch: ExtractionBatch) -> ExtractionBatch:
        model = self.session.get(ExtractionBatchModel, batch.id)
        if model is None:
            raise ValueError(f"Extraction batch {batch.id} not found")
        model.raw_entry_id = batch.raw_entry_id
        model.provider_name = batch.provider_name
        model.model_name = batch.model_name
        model.schema_version = batch.schema_version
        model.prompt_version = batch.prompt_version
        model.summary = batch.summary
        model.needs_review = batch.needs_review
        model.open_questions_json = json.dumps(batch.open_questions)
        model.created_at = batch.created_at
        self.session.flush()
        return _extraction_batch_from_model(model)


class SqlAlchemyExtractedTaskCandidateRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add_many(self, candidates: list[ExtractedTaskCandidate]) -> list[ExtractedTaskCandidate]:
        models: list[ExtractedTaskCandidateModel] = []
        for candidate in candidates:
            model = ExtractedTaskCandidateModel(
                id=candidate.id,
                extraction_batch_id=candidate.extraction_batch_id,
                title=candidate.title,
                details=candidate.details,
                project_or_group=candidate.project_or_group,
                priority=candidate.priority,
                effort=candidate.effort,
                energy=candidate.energy,
                labels_json=json.dumps(candidate.labels),
                due_date=candidate.due_date,
                parent_task_title=candidate.parent_task_title,
                confidence=candidate.confidence,
                source_excerpt=candidate.source_excerpt,
                candidate_status=candidate.candidate_status,
            )
            models.append(model)
            self.session.add(model)
        self.session.flush()
        return [_candidate_from_model(model) for model in models]

    def list_for_extraction(self, extraction_batch_id: str) -> list[ExtractedTaskCandidate]:
        models = self.session.scalars(
            select(ExtractedTaskCandidateModel)
            .where(ExtractedTaskCandidateModel.extraction_batch_id == extraction_batch_id)
            .order_by(ExtractedTaskCandidateModel.id.asc())
        ).all()
        return [_candidate_from_model(model) for model in models]

    def update_many(self, candidates: list[ExtractedTaskCandidate]) -> list[ExtractedTaskCandidate]:
        updated: list[ExtractedTaskCandidate] = []
        for candidate in candidates:
            model = self.session.get(ExtractedTaskCandidateModel, candidate.id)
            if model is None:
                raise ValueError(f"Candidate {candidate.id} not found")
            model.title = candidate.title
            model.details = candidate.details
            model.project_or_group = candidate.project_or_group
            model.priority = candidate.priority
            model.effort = candidate.effort
            model.energy = candidate.energy
            model.labels_json = json.dumps(candidate.labels)
            model.due_date = candidate.due_date
            model.parent_task_title = candidate.parent_task_title
            model.confidence = candidate.confidence
            model.source_excerpt = candidate.source_excerpt
            model.candidate_status = candidate.candidate_status
            updated.append(_candidate_from_model(model))
        self.session.flush()
        return updated


class SqlAlchemyTaskRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, task: Task) -> Task:
        model = TaskModel(
            id=task.id,
            title=task.title,
            details=task.details,
            project_id=task.project_id,
            status=task.status,
            priority=task.priority,
            effort=task.effort,
            energy=task.energy,
            source_raw_entry_id=task.source_raw_entry_id,
            source_extraction_batch_id=task.source_extraction_batch_id,
            created_at=task.created_at,
            updated_at=task.updated_at,
            due_date=task.due_date,
            completed_at=task.completed_at,
            parent_task_id=task.parent_task_id,
            device_id=task.device_id,
            sync_status=task.sync_status,
            is_deleted=task.is_deleted,
        )
        self.session.add(model)
        self.session.flush()
        return _task_from_model(model)

    def get(self, task_id: str) -> Task | None:
        model = self.session.get(TaskModel, task_id)
        return _task_from_model(model) if model else None

    def list_active(self) -> list[Task]:
        models = self.session.scalars(
            select(TaskModel).where(TaskModel.is_deleted.is_(False), TaskModel.status != "completed").order_by(TaskModel.created_at.desc())
        ).all()
        return [_task_from_model(model) for model in models]

    def list_all(self) -> list[Task]:
        models = self.session.scalars(
            select(TaskModel).where(TaskModel.is_deleted.is_(False)).order_by(TaskModel.created_at.desc())
        ).all()
        return [_task_from_model(model) for model in models]

    def update(self, task: Task) -> Task:
        model = self.session.get(TaskModel, task.id)
        if model is None:
            raise ValueError(f"Task {task.id} not found")

        model.title = task.title
        model.details = task.details
        model.project_id = task.project_id
        model.status = task.status
        model.priority = task.priority
        model.effort = task.effort
        model.energy = task.energy
        model.source_raw_entry_id = task.source_raw_entry_id
        model.source_extraction_batch_id = task.source_extraction_batch_id
        model.created_at = task.created_at
        model.updated_at = task.updated_at
        model.due_date = task.due_date
        model.completed_at = task.completed_at
        model.parent_task_id = task.parent_task_id
        model.device_id = task.device_id
        model.sync_status = task.sync_status
        model.is_deleted = task.is_deleted
        self.session.flush()
        return _task_from_model(model)


class SqlAlchemyProjectRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, project: Project) -> Project:
        model = ProjectModel(
            id=project.id,
            name=project.name,
            description=project.description,
            color_token=project.color_token,
            created_at=project.created_at,
            updated_at=project.updated_at,
            is_archived=project.is_archived,
        )
        self.session.add(model)
        self.session.flush()
        return _project_from_model(model)

    def list_all(self) -> list[Project]:
        models = self.session.scalars(select(ProjectModel).order_by(ProjectModel.name.asc())).all()
        return [_project_from_model(model) for model in models]

    def get(self, project_id: str) -> Project | None:
        model = self.session.get(ProjectModel, project_id)
        return _project_from_model(model) if model else None

    def update(self, project: Project) -> Project:
        model = self.session.get(ProjectModel, project.id)
        if model is None:
            raise ValueError(f"Project {project.id} not found")
        model.name = project.name
        model.description = project.description
        model.color_token = project.color_token
        model.created_at = project.created_at
        model.updated_at = project.updated_at
        model.is_archived = project.is_archived
        self.session.flush()
        return _project_from_model(model)


class SqlAlchemyActivityEventRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, event: ActivityEvent) -> ActivityEvent:
        model = ActivityEventModel(
            id=event.id,
            event_type=event.event_type,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            metadata_json=json.dumps(event.metadata),
            created_at=event.created_at,
            device_id=event.device_id,
        )
        self.session.add(model)
        self.session.flush()
        return _activity_from_model(model)

    def list_recent(self, limit: int = 50) -> list[ActivityEvent]:
        models = self.session.scalars(
            select(ActivityEventModel).order_by(ActivityEventModel.created_at.desc()).limit(limit)
        ).all()
        return [_activity_from_model(model) for model in models]

    def list_all(self) -> list[ActivityEvent]:
        models = self.session.scalars(select(ActivityEventModel).order_by(ActivityEventModel.created_at.desc())).all()
        return [_activity_from_model(model) for model in models]


class SqlAlchemyRecommendationSnapshotRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, snapshot: RecommendationSnapshot) -> RecommendationSnapshot:
        model = RecommendationSnapshotModel(
            id=snapshot.id,
            snapshot_kind=snapshot.snapshot_kind,
            payload_json=json.dumps(snapshot.payload),
            window_start=snapshot.window_start,
            window_end=snapshot.window_end,
            generated_at=snapshot.generated_at,
        )
        self.session.add(model)
        self.session.flush()
        return _recommendation_snapshot_from_model(model)

    def list_recent(self, snapshot_kind: str | None = None, limit: int = 20) -> list[RecommendationSnapshot]:
        statement = select(RecommendationSnapshotModel)
        if snapshot_kind is not None:
            statement = statement.where(RecommendationSnapshotModel.snapshot_kind == snapshot_kind)
        models = self.session.scalars(
            statement.order_by(RecommendationSnapshotModel.generated_at.desc()).limit(limit)
        ).all()
        return [_recommendation_snapshot_from_model(model) for model in models]


class SqlAlchemyGardenStateRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_current(self) -> GardenState | None:
        model = self.session.scalars(select(GardenStateModel).limit(1)).first()
        return _garden_state_from_model(model) if model else None

    def replace(self, state: GardenState) -> GardenState:
        existing = self.session.scalars(select(GardenStateModel)).all()
        for model in existing:
            self.session.delete(model)
        model = GardenStateModel(
            id=state.id,
            baseline_key=state.baseline_key,
            stage_key=state.stage_key,
            total_xp=state.total_xp,
            current_level=state.current_level,
            total_growth_units=state.total_growth_units,
            total_decay_points=state.total_decay_points,
            active_task_count=state.active_task_count,
            overdue_task_count=state.overdue_task_count,
            restored_tile_count=state.restored_tile_count,
            healthy_tile_count=state.healthy_tile_count,
            lush_tile_count=state.lush_tile_count,
            health_score=state.health_score,
            last_recomputed_at=state.last_recomputed_at,
        )
        self.session.add(model)
        self.session.flush()
        return _garden_state_from_model(model)


class SqlAlchemyGardenZoneRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_all(self) -> list[GardenZone]:
        models = self.session.scalars(select(GardenZoneModel).order_by(GardenZoneModel.sort_order.asc())).all()
        return [_garden_zone_from_model(model) for model in models]

    def replace_all(self, zones: list[GardenZone]) -> list[GardenZone]:
        existing = self.session.scalars(select(GardenZoneModel)).all()
        for model in existing:
            self.session.delete(model)
        created: list[GardenZoneModel] = []
        for zone in zones:
            model = GardenZoneModel(
                id=zone.id,
                name=zone.name,
                zone_key=zone.zone_key,
                sort_order=zone.sort_order,
                tile_count=zone.tile_count,
                unlocked_at=zone.unlocked_at,
            )
            self.session.add(model)
            created.append(model)
        self.session.flush()
        return [_garden_zone_from_model(model) for model in created]


class SqlAlchemyGardenTileRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_all(self) -> list[GardenTile]:
        models = self.session.scalars(
            select(GardenTileModel).order_by(GardenTileModel.coord_y.asc(), GardenTileModel.coord_x.asc())
        ).all()
        return [_garden_tile_from_model(model) for model in models]

    def replace_all(self, tiles: list[GardenTile]) -> list[GardenTile]:
        existing = self.session.scalars(select(GardenTileModel)).all()
        for model in existing:
            self.session.delete(model)
        created: list[GardenTileModel] = []
        for tile in tiles:
            model = GardenTileModel(
                id=tile.id,
                zone_id=tile.zone_id,
                tile_index=tile.tile_index,
                coord_x=tile.coord_x,
                coord_y=tile.coord_y,
                tile_state=tile.tile_state,
                growth_units=tile.growth_units,
                decay_points=tile.decay_points,
                last_changed_at=tile.last_changed_at,
            )
            self.session.add(model)
            created.append(model)
        self.session.flush()
        return [_garden_tile_from_model(model) for model in created]


class SqlAlchemyPlantInstanceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_all(self) -> list[PlantInstance]:
        models = self.session.scalars(select(PlantInstanceModel).order_by(PlantInstanceModel.id.asc())).all()
        return [_plant_instance_from_model(model) for model in models]

    def replace_all(self, items: list[PlantInstance]) -> list[PlantInstance]:
        existing = self.session.scalars(select(PlantInstanceModel)).all()
        for model in existing:
            self.session.delete(model)
        created: list[PlantInstanceModel] = []
        for item in items:
            model = PlantInstanceModel(
                id=item.id,
                garden_tile_id=item.garden_tile_id,
                plant_key=item.plant_key,
                growth_stage=item.growth_stage,
                unlocked_at=item.unlocked_at,
            )
            self.session.add(model)
            created.append(model)
        self.session.flush()
        return [_plant_instance_from_model(model) for model in created]


class SqlAlchemyDecorationInstanceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_all(self) -> list[DecorationInstance]:
        models = self.session.scalars(select(DecorationInstanceModel).order_by(DecorationInstanceModel.id.asc())).all()
        return [_decoration_instance_from_model(model) for model in models]

    def replace_all(self, items: list[DecorationInstance]) -> list[DecorationInstance]:
        existing = self.session.scalars(select(DecorationInstanceModel)).all()
        for model in existing:
            self.session.delete(model)
        created: list[DecorationInstanceModel] = []
        for item in items:
            model = DecorationInstanceModel(
                id=item.id,
                garden_tile_id=item.garden_tile_id,
                decoration_key=item.decoration_key,
                variant_key=item.variant_key,
                unlocked_at=item.unlocked_at,
            )
            self.session.add(model)
            created.append(model)
        self.session.flush()
        return [_decoration_instance_from_model(model) for model in created]


class SqlAlchemyXPLedgerRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_all(self) -> list[XPLedgerEntry]:
        models = self.session.scalars(select(XPLedgerEntryModel).order_by(XPLedgerEntryModel.awarded_at.asc())).all()
        return [_xp_ledger_from_model(model) for model in models]

    def replace_all(self, entries: list[XPLedgerEntry]) -> list[XPLedgerEntry]:
        existing = self.session.scalars(select(XPLedgerEntryModel)).all()
        for model in existing:
            self.session.delete(model)
        created: list[XPLedgerEntryModel] = []
        for entry in entries:
            model = XPLedgerEntryModel(
                id=entry.id,
                task_id=entry.task_id,
                xp_amount=entry.xp_amount,
                effort_value=entry.effort_value,
                priority_bonus=entry.priority_bonus,
                streak_multiplier=entry.streak_multiplier,
                awarded_at=entry.awarded_at,
            )
            self.session.add(model)
            created.append(model)
        self.session.flush()
        return [_xp_ledger_from_model(model) for model in created]


class SqlAlchemyUnlockLedgerRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_all(self) -> list[UnlockLedgerEntry]:
        models = self.session.scalars(select(UnlockLedgerEntryModel).order_by(UnlockLedgerEntryModel.unlocked_at.asc())).all()
        return [_unlock_ledger_from_model(model) for model in models]

    def replace_all(self, entries: list[UnlockLedgerEntry]) -> list[UnlockLedgerEntry]:
        existing = self.session.scalars(select(UnlockLedgerEntryModel)).all()
        for model in existing:
            self.session.delete(model)
        created: list[UnlockLedgerEntryModel] = []
        for entry in entries:
            model = UnlockLedgerEntryModel(
                id=entry.id,
                unlock_key=entry.unlock_key,
                unlock_type=entry.unlock_type,
                threshold_value=entry.threshold_value,
                unlocked_at=entry.unlocked_at,
            )
            self.session.add(model)
            created.append(model)
        self.session.flush()
        return [_unlock_ledger_from_model(model) for model in created]


class SqlAlchemyDecayEventRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_all(self) -> list[DecayEvent]:
        models = self.session.scalars(select(DecayEventModel).order_by(DecayEventModel.recorded_at.asc())).all()
        return [_decay_event_from_model(model) for model in models]

    def replace_all(self, entries: list[DecayEvent]) -> list[DecayEvent]:
        existing = self.session.scalars(select(DecayEventModel)).all()
        for model in existing:
            self.session.delete(model)
        created: list[DecayEventModel] = []
        for entry in entries:
            model = DecayEventModel(
                id=entry.id,
                task_id=entry.task_id,
                task_title=entry.task_title,
                days_overdue=entry.days_overdue,
                decay_points=entry.decay_points,
                recorded_at=entry.recorded_at,
            )
            self.session.add(model)
            created.append(model)
        self.session.flush()
        return [_decay_event_from_model(model) for model in created]


class SqlAlchemyRecoveryEventRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_all(self) -> list[RecoveryEvent]:
        models = self.session.scalars(select(RecoveryEventModel).order_by(RecoveryEventModel.recorded_at.asc())).all()
        return [_recovery_event_from_model(model) for model in models]

    def replace_all(self, entries: list[RecoveryEvent]) -> list[RecoveryEvent]:
        existing = self.session.scalars(select(RecoveryEventModel)).all()
        for model in existing:
            self.session.delete(model)
        created: list[RecoveryEventModel] = []
        for entry in entries:
            model = RecoveryEventModel(
                id=entry.id,
                task_id=entry.task_id,
                task_title=entry.task_title,
                recovery_points=entry.recovery_points,
                xp_amount=entry.xp_amount,
                recorded_at=entry.recorded_at,
            )
            self.session.add(model)
            created.append(model)
        self.session.flush()
        return [_recovery_event_from_model(model) for model in created]


class SqlAlchemySettingsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_local_settings(self) -> dict[str, str | bool | None]:
        models = self.session.scalars(select(AppSettingModel)).all()
        result: dict[str, str | bool | None] = {}
        for model in models:
            result[model.key] = json.loads(model.value) if model.value is not None else None
        return result

    def save_local_settings(self, values: dict[str, str | bool | None]) -> dict[str, str | bool | None]:
        existing = {
            model.key: model
            for model in self.session.scalars(
                select(AppSettingModel).where(AppSettingModel.key.in_(list(values.keys())))
            ).all()
        }

        for key, value in values.items():
            model = existing.get(key)
            if model is None:
                model = AppSettingModel(key=key, updated_at=utcnow())
                self.session.add(model)
            model.value = json.dumps(value) if value is not None else None
            model.updated_at = utcnow()
        self.session.flush()
        return self.get_local_settings()


class SqlAlchemyDeviceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, device_id: str) -> Device | None:
        model = self.session.get(DeviceModel, device_id)
        return _device_from_model(model) if model else None

    def list_all(self) -> list[Device]:
        models = self.session.scalars(select(DeviceModel).order_by(DeviceModel.registered_at.asc())).all()
        return [_device_from_model(model) for model in models]

    def upsert(self, device: Device) -> Device:
        model = self.session.get(DeviceModel, device.id)
        if model is None:
            model = DeviceModel(id=device.id)
            self.session.add(model)
        model.device_name = device.device_name
        model.platform = device.platform
        model.app_version = device.app_version
        model.registered_at = device.registered_at
        model.last_seen_at = device.last_seen_at
        model.last_sync_at = device.last_sync_at
        model.is_active = device.is_active
        self.session.flush()
        return _device_from_model(model)


class SqlAlchemyChangeEventRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, event: ChangeEvent) -> ChangeEvent:
        model = ChangeEventModel(
            event_id=event.event_id,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            change_type=event.change_type,
            changed_at=event.changed_at,
            device_id=event.device_id,
            payload_json=json.dumps(event.payload),
        )
        self.session.add(model)
        self.session.flush()
        return _change_event_from_model(model)

    def get_by_event_id(self, event_id: str) -> ChangeEvent | None:
        model = self.session.scalars(select(ChangeEventModel).where(ChangeEventModel.event_id == event_id)).first()
        return _change_event_from_model(model) if model else None

    def list_after(self, sequence: int, limit: int = 100) -> list[ChangeEvent]:
        models = self.session.scalars(
            select(ChangeEventModel)
            .where(ChangeEventModel.sequence > sequence)
            .order_by(ChangeEventModel.sequence.asc())
            .limit(limit)
        ).all()
        return [_change_event_from_model(model) for model in models]

    def latest_sequence(self) -> int:
        model = self.session.scalars(
            select(ChangeEventModel).order_by(ChangeEventModel.sequence.desc()).limit(1)
        ).first()
        return model.sequence if model else 0


class SqlAlchemySyncCursorRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_for_device(self, device_id: str, stream_key: str) -> SyncCursor | None:
        model = self.session.scalars(
            select(SyncCursorModel).where(
                SyncCursorModel.device_id == device_id,
                SyncCursorModel.stream_key == stream_key,
            )
        ).first()
        return _sync_cursor_from_model(model) if model else None

    def upsert(self, cursor: SyncCursor) -> SyncCursor:
        model = self.session.scalars(
            select(SyncCursorModel).where(
                SyncCursorModel.device_id == cursor.device_id,
                SyncCursorModel.stream_key == cursor.stream_key,
            )
        ).first()
        if model is None:
            model = SyncCursorModel(id=cursor.id)
            self.session.add(model)
        model.device_id = cursor.device_id
        model.stream_key = cursor.stream_key
        model.cursor_value = cursor.cursor_value
        model.updated_at = cursor.updated_at
        self.session.flush()
        return _sync_cursor_from_model(model)


class SqlAlchemyRecapPeriodRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert(self, period: RecapPeriod) -> RecapPeriod:
        model = self.session.get(RecapPeriodModel, period.id)
        if model is None:
            existing = self.get_for_window(period.period_type, period.window_start, period.window_end)
            model = self.session.get(RecapPeriodModel, existing.id) if existing else None
        if model is None:
            model = RecapPeriodModel(id=period.id)
            self.session.add(model)
        model.period_type = period.period_type
        model.period_label = period.period_label
        model.window_start = period.window_start
        model.window_end = period.window_end
        model.generated_at = period.generated_at
        self.session.flush()
        return _recap_period_from_model(model)

    def get(self, period_id: str) -> RecapPeriod | None:
        model = self.session.get(RecapPeriodModel, period_id)
        return _recap_period_from_model(model) if model else None

    def get_for_window(self, period_type: str, window_start: object, window_end: object) -> RecapPeriod | None:
        model = self.session.scalars(
            select(RecapPeriodModel).where(
                RecapPeriodModel.period_type == period_type,
                RecapPeriodModel.window_start == window_start,
                RecapPeriodModel.window_end == window_end,
            )
        ).first()
        return _recap_period_from_model(model) if model else None


class _ReplaceForPeriodMixin:
    model_class = None

    def _delete_existing_for_period(self, period_id: str) -> None:
        models = self.session.scalars(select(self.model_class).where(self.model_class.period_id == period_id)).all()
        for model in models:
            self.session.delete(model)


class SqlAlchemyRecapMetricSnapshotRepository(_ReplaceForPeriodMixin):
    model_class = RecapMetricSnapshotModel

    def __init__(self, session: Session) -> None:
        self.session = session

    def list_for_period(self, period_id: str) -> list[RecapMetricSnapshot]:
        models = self.session.scalars(
            select(RecapMetricSnapshotModel)
            .where(RecapMetricSnapshotModel.period_id == period_id)
            .order_by(RecapMetricSnapshotModel.sort_order.asc(), RecapMetricSnapshotModel.metric_key.asc())
        ).all()
        return [_recap_metric_from_model(model) for model in models]

    def replace_for_period(self, period_id: str, items: list[RecapMetricSnapshot]) -> list[RecapMetricSnapshot]:
        self._delete_existing_for_period(period_id)
        created: list[RecapMetricSnapshotModel] = []
        for item in items:
            model = RecapMetricSnapshotModel(
                id=item.id,
                period_id=period_id,
                metric_key=item.metric_key,
                sort_order=item.sort_order,
                numeric_value=item.numeric_value,
                text_value=item.text_value,
                json_value_json=json.dumps(item.json_value) if item.json_value else None,
            )
            self.session.add(model)
            created.append(model)
        self.session.flush()
        return [_recap_metric_from_model(model) for model in created]


class SqlAlchemyHighlightCardRepository(_ReplaceForPeriodMixin):
    model_class = HighlightCardModel

    def __init__(self, session: Session) -> None:
        self.session = session

    def list_for_period(self, period_id: str) -> list[HighlightCard]:
        models = self.session.scalars(
            select(HighlightCardModel)
            .where(HighlightCardModel.period_id == period_id)
            .order_by(HighlightCardModel.sort_order.asc(), HighlightCardModel.id.asc())
        ).all()
        return [_highlight_card_from_model(model) for model in models]

    def replace_for_period(self, period_id: str, items: list[HighlightCard]) -> list[HighlightCard]:
        self._delete_existing_for_period(period_id)
        created: list[HighlightCardModel] = []
        for item in items:
            model = HighlightCardModel(
                id=item.id,
                period_id=period_id,
                card_type=item.card_type,
                title=item.title,
                subtitle=item.subtitle,
                primary_value=item.primary_value,
                secondary_value=item.secondary_value,
                supporting_text=item.supporting_text,
                visual_hint=item.visual_hint,
                sort_order=item.sort_order,
            )
            self.session.add(model)
            created.append(model)
        self.session.flush()
        return [_highlight_card_from_model(model) for model in created]


class SqlAlchemyMilestoneRepository(_ReplaceForPeriodMixin):
    model_class = MilestoneModel

    def __init__(self, session: Session) -> None:
        self.session = session

    def list_for_period(self, period_id: str) -> list[Milestone]:
        models = self.session.scalars(
            select(MilestoneModel)
            .where(MilestoneModel.period_id == period_id)
            .order_by(MilestoneModel.sort_order.asc(), MilestoneModel.id.asc())
        ).all()
        return [_milestone_from_model(model) for model in models]

    def replace_for_period(self, period_id: str, items: list[Milestone]) -> list[Milestone]:
        self._delete_existing_for_period(period_id)
        created: list[MilestoneModel] = []
        for item in items:
            model = MilestoneModel(
                id=item.id,
                period_id=period_id,
                milestone_key=item.milestone_key,
                title=item.title,
                description=item.description,
                metric_value=item.metric_value,
                detected_at=item.detected_at,
                sort_order=item.sort_order,
            )
            self.session.add(model)
            created.append(model)
        self.session.flush()
        return [_milestone_from_model(model) for model in created]


class SqlAlchemyStreakSummaryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_for_period(self, period_id: str) -> StreakSummary | None:
        model = self.session.scalars(
            select(StreakSummaryModel).where(StreakSummaryModel.period_id == period_id)
        ).first()
        return _streak_summary_from_model(model) if model else None

    def replace_for_period(self, period_id: str, item: StreakSummary) -> StreakSummary:
        existing = self.session.scalars(
            select(StreakSummaryModel).where(StreakSummaryModel.period_id == period_id)
        ).first()
        if existing is None:
            existing = StreakSummaryModel(id=item.id, period_id=period_id)
            self.session.add(existing)
        existing.current_streak_days = item.current_streak_days
        existing.longest_streak_days = item.longest_streak_days
        existing.period_best_streak_days = item.period_best_streak_days
        existing.active_days = item.active_days
        existing.streak_start = item.streak_start
        existing.streak_end = item.streak_end
        self.session.flush()
        return _streak_summary_from_model(existing)


class SqlAlchemyProjectSummaryRepository(_ReplaceForPeriodMixin):
    model_class = ProjectSummaryModel

    def __init__(self, session: Session) -> None:
        self.session = session

    def list_for_period(self, period_id: str) -> list[ProjectSummary]:
        models = self.session.scalars(
            select(ProjectSummaryModel)
            .where(ProjectSummaryModel.period_id == period_id)
            .order_by(ProjectSummaryModel.sort_order.asc(), ProjectSummaryModel.project_name.asc())
        ).all()
        return [_project_summary_from_model(model) for model in models]

    def replace_for_period(self, period_id: str, items: list[ProjectSummary]) -> list[ProjectSummary]:
        self._delete_existing_for_period(period_id)
        created: list[ProjectSummaryModel] = []
        for item in items:
            model = ProjectSummaryModel(
                id=item.id,
                period_id=period_id,
                project_id=item.project_id,
                project_name=item.project_name,
                completed_task_count=item.completed_task_count,
                xp_gained=item.xp_gained,
                completion_share=item.completion_share,
                effort_small_count=item.effort_small_count,
                effort_medium_count=item.effort_medium_count,
                effort_large_count=item.effort_large_count,
                latest_completion_at=item.latest_completion_at,
                sort_order=item.sort_order,
            )
            self.session.add(model)
            created.append(model)
        self.session.flush()
        return [_project_summary_from_model(model) for model in created]


class SqlAlchemyRecapNarrativeRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_for_period(self, period_id: str) -> RecapNarrative | None:
        model = self.session.scalars(
            select(RecapNarrativeModel).where(RecapNarrativeModel.period_id == period_id)
        ).first()
        return _recap_narrative_from_model(model) if model else None

    def upsert_for_period(self, narrative: RecapNarrative) -> RecapNarrative:
        model = self.session.scalars(
            select(RecapNarrativeModel).where(RecapNarrativeModel.period_id == narrative.period_id)
        ).first()
        if model is None:
            model = RecapNarrativeModel(id=narrative.id, period_id=narrative.period_id)
            self.session.add(model)
        model.generation_status = narrative.generation_status
        model.provider_name = narrative.provider_name
        model.model_name = narrative.model_name
        model.prompt_version = narrative.prompt_version
        model.source_summary_version = narrative.source_summary_version
        model.source_summary_hash = narrative.source_summary_hash
        model.generated_at = narrative.generated_at
        model.narrative_text = narrative.narrative_text
        model.error_metadata_json = json.dumps(narrative.error_metadata) if narrative.error_metadata else None
        self.session.flush()
        return _recap_narrative_from_model(model)
