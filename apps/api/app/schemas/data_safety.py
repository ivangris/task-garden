from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class DataBackupResponse(BaseModel):
    name: str
    backup_type: Literal["manual", "pre_restore"]
    size_bytes: int
    created_at: datetime
    alembic_revision: str | None = None
    integrity_status: Literal["ok", "invalid"]


class DataSafetyStatusResponse(BaseModel):
    available: bool
    database_kind: str
    database_exists: bool = False
    database_path: str | None = None
    backup_directory: str | None = None
    reason: str | None = None
    backups: list[DataBackupResponse] = Field(default_factory=list)


class RestoreDataBackupRequest(BaseModel):
    backup_name: str = Field(min_length=1, max_length=255)
    confirmation: Literal["RESTORE"]

    @field_validator("backup_name")
    @classmethod
    def validate_backup_name(cls, value: str) -> str:
        if "/" in value or "\\" in value or value in {".", ".."}:
            raise ValueError("Choose a backup by name, not by filesystem path.")
        if not value.startswith("task-garden-") or not value.endswith(".db"):
            raise ValueError("Backup name is not a Task Garden database backup.")
        return value


class RestoreDataBackupResponse(BaseModel):
    restored_from: DataBackupResponse
    safety_backup: DataBackupResponse
    restored_at: datetime
    message: str
