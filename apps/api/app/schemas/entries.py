from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import EntryStatus, SourceType


class CreateEntryRequest(BaseModel):
    source_type: SourceType = "typed"
    raw_text: str = Field(min_length=1, max_length=20000)
    device_id: str | None = Field(default=None, max_length=64)


class RawEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_type: SourceType
    raw_text: str
    audio_file_ref: str | None = None
    entry_status: EntryStatus
    device_id: str | None = None
    created_at: datetime
    updated_at: datetime


class RawEntryListResponse(BaseModel):
    items: list[RawEntryResponse]
