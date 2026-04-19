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

