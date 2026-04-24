from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DeviceRegistrationRequest(BaseModel):
    device_id: str | None = None
    device_name: str = Field(min_length=1, max_length=255)
    platform: str = Field(min_length=1, max_length=128)
    app_version: str | None = Field(default=None, max_length=64)


class DeviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    device_name: str
    platform: str
    app_version: str | None = None
    registered_at: datetime
    last_seen_at: datetime
    last_sync_at: datetime | None = None
    is_active: bool


class ChangeEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sequence: int
    event_id: str
    entity_type: str
    entity_id: str
    change_type: str
    changed_at: datetime
    device_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class PushChangeEventRequest(BaseModel):
    event_id: str
    entity_type: str
    entity_id: str
    change_type: str
    changed_at: datetime
    device_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class SyncPushRequest(BaseModel):
    device_id: str
    changes: list[PushChangeEventRequest]


class SyncPushResponse(BaseModel):
    accepted_count: int
    duplicate_count: int
    applied_count: int
    latest_sequence: int


class SyncPullResponse(BaseModel):
    device_id: str
    cursor: int
    next_cursor: int
    has_more: bool
    items: list[ChangeEventResponse]


class SyncStatusResponse(BaseModel):
    provider_name: str
    sync_enabled: bool
    current_device: DeviceResponse | None = None
    registered_device_count: int
    latest_sequence: int
    last_pull_cursor: int | None = None
    last_sync_at: datetime | None = None
