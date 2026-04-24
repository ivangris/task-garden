from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import EntryStatus, SourceType


class CreateEntryRequest(BaseModel):
    source_type: SourceType = "typed"
    raw_text: str = Field(min_length=1, max_length=20000)
    device_id: str | None = Field(default=None, max_length=64)


class CreateAudioEntryRequest(BaseModel):
    device_id: str | None = Field(default=None, max_length=64)


class TranscriptSegmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    raw_entry_id: str
    segment_index: int
    start_ms: int | None = None
    end_ms: int | None = None
    text: str
    speaker_label: str | None = None


class RawEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_type: SourceType
    raw_text: str
    audio_file_ref: str | None = None
    transcript_provider_name: str | None = None
    transcript_model_name: str | None = None
    transcript_metadata: dict[str, Any] = Field(default_factory=dict)
    entry_status: EntryStatus
    device_id: str | None = None
    created_at: datetime
    updated_at: datetime


class RawEntryListResponse(BaseModel):
    items: list[RawEntryResponse]


class TranscriptionResponse(BaseModel):
    raw_entry: RawEntryResponse
    segments: list[TranscriptSegmentResponse]
