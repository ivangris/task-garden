from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, File, Header, UploadFile

from app.config import Settings, get_settings
from app.db.session import get_db
from app.repositories.sqlalchemy import (
    SqlAlchemyActivityEventRepository,
    SqlAlchemyChangeEventRepository,
    SqlAlchemyRawEntryRepository,
    SqlAlchemySettingsRepository,
    SqlAlchemyTranscriptSegmentRepository,
)
from app.schemas.entries import (
    CreateAudioEntryRequest,
    CreateEntryRequest,
    RawEntryListResponse,
    RawEntryResponse,
    TranscriptSegmentResponse,
    TranscriptionResponse,
)
from app.services.entries import archive_raw_entry, create_audio_entry_shell, create_raw_entry, get_raw_entry
from app.services.settings import get_settings_payload
from app.services.sync import record_change_event, snapshot_raw_entry
from app.services.transcription import transcribe_audio_entry

router = APIRouter()


@router.post("", response_model=RawEntryResponse, status_code=201)
def post_entry(
    payload: CreateEntryRequest,
    db: Session = Depends(get_db),
    device_id: str | None = Header(default=None, alias="X-Task-Garden-Device-Id"),
) -> RawEntryResponse:
    effective_payload = payload.model_copy(update={"device_id": payload.device_id or device_id})
    entry = create_raw_entry(
        effective_payload,
        SqlAlchemyRawEntryRepository(db),
        SqlAlchemyActivityEventRepository(db),
    )
    record_change_event(
        SqlAlchemyChangeEventRepository(db),
        entity_type="raw_entry",
        entity_id=entry.id,
        change_type="upserted",
        payload=snapshot_raw_entry(entry),
        device_id=device_id or entry.device_id,
    )
    db.commit()
    return RawEntryResponse.model_validate(entry)


@router.post("/audio", response_model=RawEntryResponse, status_code=201)
def post_audio_entry(
    payload: CreateAudioEntryRequest,
    db: Session = Depends(get_db),
    device_id: str | None = Header(default=None, alias="X-Task-Garden-Device-Id"),
) -> RawEntryResponse:
    effective_payload = payload.model_copy(update={"device_id": payload.device_id or device_id})
    entry = create_audio_entry_shell(
        effective_payload,
        SqlAlchemyRawEntryRepository(db),
        SqlAlchemyActivityEventRepository(db),
    )
    record_change_event(
        SqlAlchemyChangeEventRepository(db),
        entity_type="raw_entry",
        entity_id=entry.id,
        change_type="upserted",
        payload=snapshot_raw_entry(entry),
        device_id=device_id or entry.device_id,
    )
    db.commit()
    return RawEntryResponse.model_validate(entry)


@router.post("/{entry_id}/transcribe", response_model=TranscriptionResponse)
async def post_transcribe_entry(
    entry_id: str,
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    device_id: str | None = Header(default=None, alias="X-Task-Garden-Device-Id"),
) -> TranscriptionResponse:
    effective_settings = settings.model_copy(
        update=get_settings_payload(SqlAlchemySettingsRepository(db), settings).model_dump(exclude={"stt_ready"})
    )
    entry, segments = transcribe_audio_entry(
        entry_id,
        audio_bytes=await audio.read(),
        file_name=audio.filename,
        content_type=audio.content_type,
        settings=effective_settings,
        raw_entries=SqlAlchemyRawEntryRepository(db),
        transcript_segments=SqlAlchemyTranscriptSegmentRepository(db),
        activity_events=SqlAlchemyActivityEventRepository(db),
    )
    record_change_event(
        SqlAlchemyChangeEventRepository(db),
        entity_type="raw_entry",
        entity_id=entry.id,
        change_type="updated",
        payload=snapshot_raw_entry(entry),
        device_id=device_id or entry.device_id,
    )
    db.commit()
    return TranscriptionResponse(
        raw_entry=RawEntryResponse.model_validate(entry),
        segments=[TranscriptSegmentResponse.model_validate(segment) for segment in segments],
    )


@router.get("/{entry_id}", response_model=RawEntryResponse)
def fetch_entry(entry_id: str, db: Session = Depends(get_db)) -> RawEntryResponse:
    entry = get_raw_entry(entry_id, SqlAlchemyRawEntryRepository(db))
    return RawEntryResponse.model_validate(entry)


@router.get("", response_model=RawEntryListResponse)
def list_entries(db: Session = Depends(get_db)) -> RawEntryListResponse:
    entries = SqlAlchemyRawEntryRepository(db).list_all()
    return RawEntryListResponse(items=[RawEntryResponse.model_validate(entry) for entry in entries])


@router.delete("/{entry_id}", response_model=RawEntryResponse)
def delete_entry(
    entry_id: str,
    db: Session = Depends(get_db),
    device_id: str | None = Header(default=None, alias="X-Task-Garden-Device-Id"),
) -> RawEntryResponse:
    entry = archive_raw_entry(
        entry_id,
        SqlAlchemyRawEntryRepository(db),
        SqlAlchemyActivityEventRepository(db),
    )
    record_change_event(
        SqlAlchemyChangeEventRepository(db),
        entity_type="raw_entry",
        entity_id=entry.id,
        change_type="archived",
        payload=snapshot_raw_entry(entry),
        device_id=device_id or entry.device_id,
    )
    db.commit()
    return RawEntryResponse.model_validate(entry)
