from __future__ import annotations

from datetime import datetime

from app.config import Settings
from app.domain.entities import ChangeEvent, Device, GardenState, Project, RawEntry, SyncCursor, Task
from app.repositories.interfaces import (
    ChangeEventRepository,
    DeviceRepository,
    GardenStateRepository,
    ProjectRepository,
    RawEntryRepository,
    SettingsRepository,
    SyncCursorRepository,
    TaskRepository,
)
from app.schemas.entries import RawEntryResponse
from app.schemas.garden import GardenStateResponse
from app.schemas.projects import ProjectResponse
from app.schemas.recaps import RecapNarrativeResponse
from app.schemas.settings import AppSettingsResponse
from app.schemas.sync import (
    ChangeEventResponse,
    DeviceRegistrationRequest,
    DeviceResponse,
    PushChangeEventRequest,
    SyncPullResponse,
    SyncPushResponse,
    SyncStatusResponse,
)
from app.schemas.tasks import TaskResponse
from app.services.common import generate_id, utcnow
from app.services.settings import get_settings_payload


SYNC_STREAM_KEY = "change_events"


def register_device(
    payload: DeviceRegistrationRequest,
    devices: DeviceRepository,
) -> Device:
    now = utcnow()
    existing = devices.get(payload.device_id) if payload.device_id else None
    if existing is None:
        device = Device(
            id=payload.device_id or generate_id(),
            device_name=payload.device_name.strip(),
            platform=payload.platform.strip(),
            app_version=payload.app_version,
            registered_at=now,
            last_seen_at=now,
            last_sync_at=existing.last_sync_at if existing else None,
            is_active=True,
        )
    else:
        existing.device_name = payload.device_name.strip()
        existing.platform = payload.platform.strip()
        existing.app_version = payload.app_version
        existing.last_seen_at = now
        existing.is_active = True
        device = existing
    return devices.upsert(device)


def record_change_event(
    repository: ChangeEventRepository,
    *,
    entity_type: str,
    entity_id: str,
    change_type: str,
    payload: dict[str, object],
    device_id: str | None,
    changed_at: datetime | None = None,
    event_id: str | None = None,
) -> ChangeEvent:
    event = ChangeEvent(
        sequence=0,
        event_id=event_id or generate_id(),
        entity_type=entity_type,
        entity_id=entity_id,
        change_type=change_type,
        changed_at=changed_at or utcnow(),
        device_id=device_id,
        payload=payload,
    )
    return repository.add(event)


def snapshot_task(task: Task, project_name: str | None = None) -> dict[str, object]:
    return TaskResponse.model_validate(task).model_copy(update={"project_name": project_name}).model_dump(mode="json")


def snapshot_project(project: Project) -> dict[str, object]:
    return ProjectResponse.model_validate(project).model_dump(mode="json")


def snapshot_raw_entry(entry: RawEntry) -> dict[str, object]:
    return RawEntryResponse.model_validate(entry).model_dump(mode="json")


def snapshot_garden_state(state: GardenState) -> dict[str, object]:
    return GardenStateResponse.model_validate(state).model_dump(mode="json")


def snapshot_settings(payload: AppSettingsResponse) -> dict[str, object]:
    return payload.model_dump(mode="json")


def snapshot_recap_narrative(payload: RecapNarrativeResponse) -> dict[str, object]:
    return payload.model_dump(mode="json")


def pull_changes(
    *,
    device_id: str,
    cursor_value: int | None,
    limit: int,
    change_events: ChangeEventRepository,
    cursors: SyncCursorRepository,
    devices: DeviceRepository,
) -> SyncPullResponse:
    existing_cursor = cursors.get_for_device(device_id, SYNC_STREAM_KEY)
    current_cursor = cursor_value if cursor_value is not None else (existing_cursor.cursor_value if existing_cursor else 0)
    items = change_events.list_after(current_cursor, limit=limit + 1)
    visible_items = items[:limit]
    next_cursor = visible_items[-1].sequence if visible_items else current_cursor
    has_more = len(items) > limit
    cursors.upsert(
        SyncCursor(
            id=existing_cursor.id if existing_cursor else generate_id(),
            device_id=device_id,
            stream_key=SYNC_STREAM_KEY,
            cursor_value=next_cursor,
            updated_at=utcnow(),
        )
    )
    device = devices.get(device_id)
    if device is not None:
        device.last_seen_at = utcnow()
        device.last_sync_at = utcnow()
        devices.upsert(device)
    return SyncPullResponse(
        device_id=device_id,
        cursor=current_cursor,
        next_cursor=next_cursor,
        has_more=has_more,
        items=[ChangeEventResponse.model_validate(item) for item in visible_items],
    )


def _should_apply(incoming_changed_at: datetime, current_changed_at: datetime | None) -> bool:
    if current_changed_at is None:
        return True
    return incoming_changed_at >= current_changed_at


def _apply_task_change(change: PushChangeEventRequest, tasks: TaskRepository) -> bool:
    payload = change.payload
    current = tasks.get(change.entity_id)
    current_changed_at = current.updated_at if current else None
    if not _should_apply(change.changed_at, current_changed_at):
        return False
    task = Task(
        id=change.entity_id,
        title=str(payload.get("title", "")).strip(),
        details=payload.get("details"),
        project_id=payload.get("project_id"),
        status=str(payload.get("status", "inbox")),
        priority=str(payload.get("priority", "medium")),
        effort=str(payload.get("effort", "medium")),
        energy=str(payload.get("energy", "medium")),
        source_raw_entry_id=payload.get("source_raw_entry_id"),
        created_at=datetime.fromisoformat(str(payload.get("created_at"))) if payload.get("created_at") else change.changed_at,
        updated_at=datetime.fromisoformat(str(payload.get("updated_at"))) if payload.get("updated_at") else change.changed_at,
        due_date=datetime.fromisoformat(str(payload.get("due_date"))) if payload.get("due_date") else None,
        completed_at=datetime.fromisoformat(str(payload.get("completed_at"))) if payload.get("completed_at") else None,
        device_id=payload.get("device_id"),
    )
    if current is None:
        tasks.add(task)
    else:
        task.source_extraction_batch_id = current.source_extraction_batch_id
        task.parent_task_id = current.parent_task_id
        task.sync_status = current.sync_status
        task.is_deleted = current.is_deleted
        tasks.update(task)
    return True


def _apply_project_change(change: PushChangeEventRequest, projects: ProjectRepository) -> bool:
    payload = change.payload
    current = projects.get(change.entity_id)
    current_changed_at = current.updated_at if current else None
    if not _should_apply(change.changed_at, current_changed_at):
        return False
    project = Project(
        id=change.entity_id,
        name=str(payload.get("name", "")).strip(),
        description=payload.get("description"),
        color_token=payload.get("color_token"),
        is_archived=bool(payload.get("is_archived", False)),
        created_at=datetime.fromisoformat(str(payload.get("created_at"))) if payload.get("created_at") else change.changed_at,
        updated_at=datetime.fromisoformat(str(payload.get("updated_at"))) if payload.get("updated_at") else change.changed_at,
    )
    if current is None:
        projects.add(project)
    else:
        projects.update(project)
    return True


def _apply_raw_entry_change(change: PushChangeEventRequest, raw_entries: RawEntryRepository) -> bool:
    payload = change.payload
    current = raw_entries.get(change.entity_id)
    current_changed_at = current.updated_at if current else None
    if not _should_apply(change.changed_at, current_changed_at):
        return False
    entry = RawEntry(
        id=change.entity_id,
        source_type=str(payload.get("source_type", "typed")),
        raw_text=str(payload.get("raw_text", "")),
        audio_file_ref=payload.get("audio_file_ref"),
        transcript_provider_name=payload.get("transcript_provider_name"),
        transcript_model_name=payload.get("transcript_model_name"),
        transcript_metadata=payload.get("transcript_metadata") or {},
        entry_status=str(payload.get("entry_status", "new")),
        device_id=payload.get("device_id"),
        created_at=datetime.fromisoformat(str(payload.get("created_at"))) if payload.get("created_at") else change.changed_at,
        updated_at=datetime.fromisoformat(str(payload.get("updated_at"))) if payload.get("updated_at") else change.changed_at,
    )
    if current is None:
        raw_entries.add(entry)
    else:
        raw_entries.update(entry)
    return True


def _apply_settings_change(change: PushChangeEventRequest, settings_repo: SettingsRepository, defaults: Settings) -> bool:
    allowed = set(AppSettingsResponse.model_fields.keys())
    filtered = {key: value for key, value in change.payload.items() if key in allowed}
    if not filtered:
        return False
    current = get_settings_payload(settings_repo, defaults).model_dump()
    if current == {**current, **filtered}:
        return False
    settings_repo.save_local_settings(filtered)
    return True


def _apply_garden_state_change(change: PushChangeEventRequest, garden_states: GardenStateRepository) -> bool:
    payload = change.payload
    current = garden_states.get_current()
    current_changed_at = current.last_recomputed_at if current else None
    if not _should_apply(change.changed_at, current_changed_at):
        return False
    state = GardenState(
        id=str(payload.get("id", change.entity_id)),
        baseline_key=str(payload.get("baseline_key", "neglected_desert")),
        stage_key=str(payload.get("stage_key", "neglected_desert")),
        total_xp=int(payload.get("total_xp", 0)),
        current_level=int(payload.get("current_level", 1)),
        total_growth_units=int(payload.get("total_growth_units", 0)),
        total_decay_points=int(payload.get("total_decay_points", 0)),
        active_task_count=int(payload.get("active_task_count", 0)),
        overdue_task_count=int(payload.get("overdue_task_count", 0)),
        restored_tile_count=int(payload.get("restored_tile_count", 0)),
        healthy_tile_count=int(payload.get("healthy_tile_count", 0)),
        lush_tile_count=int(payload.get("lush_tile_count", 0)),
        health_score=int(payload.get("health_score", 0)),
        last_recomputed_at=datetime.fromisoformat(str(payload.get("last_recomputed_at")))
        if payload.get("last_recomputed_at")
        else change.changed_at,
    )
    garden_states.replace(state)
    return True


def push_changes(
    *,
    device_id: str,
    changes: list[PushChangeEventRequest],
    change_events: ChangeEventRepository,
    devices: DeviceRepository,
    cursors: SyncCursorRepository,
    tasks: TaskRepository,
    projects: ProjectRepository,
    raw_entries: RawEntryRepository,
    settings_repo: SettingsRepository,
    garden_states: GardenStateRepository,
    defaults: Settings,
) -> SyncPushResponse:
    accepted_count = 0
    duplicate_count = 0
    applied_count = 0

    for change in sorted(changes, key=lambda item: (item.changed_at, item.event_id)):
        if change_events.get_by_event_id(change.event_id) is not None:
            duplicate_count += 1
            continue

        applied = False
        if change.entity_type == "task":
            applied = _apply_task_change(change, tasks)
        elif change.entity_type == "project":
            applied = _apply_project_change(change, projects)
        elif change.entity_type == "raw_entry":
            applied = _apply_raw_entry_change(change, raw_entries)
        elif change.entity_type == "settings":
            applied = _apply_settings_change(change, settings_repo, defaults)
        elif change.entity_type == "garden_state":
            applied = _apply_garden_state_change(change, garden_states)

        record_change_event(
            change_events,
            entity_type=change.entity_type,
            entity_id=change.entity_id,
            change_type=change.change_type,
            payload=change.payload,
            device_id=change.device_id,
            changed_at=change.changed_at,
            event_id=change.event_id,
        )
        accepted_count += 1
        applied_count += 1 if applied else 0

    latest_sequence = change_events.latest_sequence()
    device = devices.get(device_id)
    if device is not None:
        device.last_seen_at = utcnow()
        device.last_sync_at = utcnow()
        devices.upsert(device)
        existing = cursors.get_for_device(device_id, SYNC_STREAM_KEY)
        cursors.upsert(
            SyncCursor(
                id=existing.id if existing else generate_id(),
                device_id=device_id,
                stream_key=SYNC_STREAM_KEY,
                cursor_value=latest_sequence,
                updated_at=utcnow(),
            )
        )

    return SyncPushResponse(
        accepted_count=accepted_count,
        duplicate_count=duplicate_count,
        applied_count=applied_count,
        latest_sequence=latest_sequence,
    )


def get_sync_status(
    *,
    device_id: str | None,
    settings: Settings,
    settings_repo: SettingsRepository,
    devices: DeviceRepository,
    change_events: ChangeEventRepository,
    cursors: SyncCursorRepository,
) -> SyncStatusResponse:
    effective_settings = get_settings_payload(settings_repo, settings)
    current_device = devices.get(device_id) if device_id else None
    cursor = cursors.get_for_device(device_id, SYNC_STREAM_KEY) if device_id else None
    return SyncStatusResponse(
        provider_name=effective_settings.sync_provider,
        sync_enabled=effective_settings.sync_provider != "local_only",
        current_device=DeviceResponse.model_validate(current_device) if current_device is not None else None,
        registered_device_count=len(devices.list_all()),
        latest_sequence=change_events.latest_sequence(),
        last_pull_cursor=cursor.cursor_value if cursor else None,
        last_sync_at=current_device.last_sync_at if current_device else None,
    )
