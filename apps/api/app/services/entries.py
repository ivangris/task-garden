from fastapi import HTTPException, status

from app.domain.entities import RawEntry
from app.repositories.interfaces import ActivityEventRepository, RawEntryRepository
from app.schemas.entries import CreateEntryRequest
from app.services.activity import log_activity
from app.services.common import generate_id, utcnow


def create_raw_entry(
    payload: CreateEntryRequest,
    raw_entries: RawEntryRepository,
    activity_events: ActivityEventRepository,
) -> RawEntry:
    now = utcnow()
    entry = RawEntry(
        id=generate_id(),
        source_type=payload.source_type,
        raw_text=payload.raw_text.strip(),
        entry_status="new",
        created_at=now,
        updated_at=now,
        device_id=payload.device_id,
    )
    created = raw_entries.add(entry)
    log_activity(
        activity_events,
        event_type="raw_entry_created",
        entity_type="raw_entry",
        entity_id=created.id,
        metadata={"source_type": created.source_type},
        device_id=created.device_id,
    )
    return created


def get_raw_entry(entry_id: str, raw_entries: RawEntryRepository) -> RawEntry:
    entry = raw_entries.get(entry_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Raw entry not found.")
    return entry

