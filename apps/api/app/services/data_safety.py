from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from uuid import uuid4

from app.config import BASE_DIR, Settings
from app.db.session import get_engine, sqlite_database_path
from app.schemas.data_safety import (
    DataBackupResponse,
    DataSafetyStatusResponse,
    RestoreDataBackupResponse,
)


BACKUP_PREFIX = "task-garden-"
BACKUP_SUFFIX = ".db"
_backup_lock = RLock()


class DataSafetyError(RuntimeError):
    pass


class DataSafetyUnavailableError(DataSafetyError):
    pass


class BackupValidationError(DataSafetyError):
    pass


def _database_kind(database_url: str) -> str:
    return database_url.split(":", maxsplit=1)[0].split("+", maxsplit=1)[0]


def _backup_directory(settings: Settings) -> Path:
    configured = Path(settings.backup_directory).expanduser()
    if not configured.is_absolute():
        configured = BASE_DIR / configured
    return configured.resolve()


def _local_sqlite_paths(settings: Settings) -> tuple[Path, Path]:
    database_path = sqlite_database_path(settings.database_url)
    if settings.hosted_mode:
        raise DataSafetyUnavailableError("Backups are managed locally and are unavailable in hosted mode.")
    if database_path is None:
        raise DataSafetyUnavailableError("Local backup and restore currently supports file-backed SQLite databases only.")
    return database_path, _backup_directory(settings)


def _read_database_metadata(database_path: Path) -> tuple[str, str | None]:
    if not database_path.exists() or not database_path.is_file():
        raise BackupValidationError(f"Database file does not exist: {database_path}")

    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(f"{database_path.resolve().as_uri()}?mode=ro", uri=True)
        integrity_row = connection.execute("PRAGMA quick_check").fetchone()
        integrity_status = str(integrity_row[0]) if integrity_row else "invalid"
        if integrity_status.lower() != "ok":
            raise BackupValidationError(f"SQLite integrity check failed: {integrity_status}")
        try:
            revision_row = connection.execute("SELECT version_num FROM alembic_version LIMIT 1").fetchone()
        except sqlite3.OperationalError:
            revision_row = None
        revision = str(revision_row[0]) if revision_row else None
        return "ok", revision
    except sqlite3.DatabaseError as error:
        raise BackupValidationError(f"SQLite integrity check failed: {error}") from error
    finally:
        if connection is not None:
            connection.close()


def _backup_type_from_name(name: str) -> str:
    return "pre_restore" if name.startswith(f"{BACKUP_PREFIX}pre-restore-") else "manual"


def _backup_response(backup_path: Path, *, allow_invalid: bool = False) -> DataBackupResponse:
    integrity_status = "ok"
    revision: str | None = None
    try:
        integrity_status, revision = _read_database_metadata(backup_path)
    except BackupValidationError:
        if not allow_invalid:
            raise
        integrity_status = "invalid"

    stat = backup_path.stat()
    return DataBackupResponse(
        name=backup_path.name,
        backup_type=_backup_type_from_name(backup_path.name),
        size_bytes=stat.st_size,
        created_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
        alembic_revision=revision,
        integrity_status=integrity_status,
    )


def _safe_backup_path(backup_directory: Path, backup_name: str) -> Path:
    resolved_directory = backup_directory.resolve()
    candidate = (resolved_directory / backup_name).resolve()
    if candidate.parent != resolved_directory:
        raise BackupValidationError("Backup path must stay inside the configured backup directory.")
    if not candidate.name.startswith(BACKUP_PREFIX) or candidate.suffix.lower() != BACKUP_SUFFIX:
        raise BackupValidationError("Backup name is not a Task Garden database backup.")
    if not candidate.exists() or not candidate.is_file():
        raise BackupValidationError("Selected backup does not exist.")
    return candidate


def _timestamped_backup_path(backup_directory: Path, backup_type: str) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    label = "pre-restore" if backup_type == "pre_restore" else "manual"
    return backup_directory / f"{BACKUP_PREFIX}{label}-{timestamp}{BACKUP_SUFFIX}"


def _write_sqlite_backup(source_path: Path, destination_path: Path) -> None:
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = destination_path.with_name(f".{destination_path.name}.{uuid4().hex}.tmp")
    try:
        source = sqlite3.connect(source_path)
        destination = sqlite3.connect(temporary_path)
        try:
            source.backup(destination)
        finally:
            destination.close()
            source.close()
        _read_database_metadata(temporary_path)
        os.replace(temporary_path, destination_path)
    finally:
        temporary_path.unlink(missing_ok=True)


def list_data_backups(settings: Settings) -> list[DataBackupResponse]:
    try:
        _, backup_directory = _local_sqlite_paths(settings)
    except DataSafetyUnavailableError:
        return []
    if not backup_directory.exists():
        return []

    backups = [
        _backup_response(path, allow_invalid=True)
        for path in backup_directory.glob(f"{BACKUP_PREFIX}*{BACKUP_SUFFIX}")
        if path.is_file()
    ]
    return sorted(backups, key=lambda backup: backup.created_at, reverse=True)


def get_data_safety_status(settings: Settings) -> DataSafetyStatusResponse:
    database_kind = _database_kind(settings.database_url)
    try:
        database_path, backup_directory = _local_sqlite_paths(settings)
    except DataSafetyUnavailableError as error:
        return DataSafetyStatusResponse(
            available=False,
            database_kind=database_kind,
            database_exists=False,
            reason=str(error),
        )

    return DataSafetyStatusResponse(
        available=True,
        database_kind=database_kind,
        database_exists=database_path.exists(),
        database_path=str(database_path),
        backup_directory=str(backup_directory),
        reason=None if database_path.exists() else "The local database will be available after first launch.",
        backups=list_data_backups(settings),
    )


def create_data_backup(settings: Settings, *, backup_type: str = "manual") -> DataBackupResponse:
    with _backup_lock:
        database_path, backup_directory = _local_sqlite_paths(settings)
        _read_database_metadata(database_path)
        backup_path = _timestamped_backup_path(backup_directory, backup_type)
        _write_sqlite_backup(database_path, backup_path)
        return _backup_response(backup_path)


def restore_data_backup(settings: Settings, backup_name: str) -> RestoreDataBackupResponse:
    with _backup_lock:
        database_path, backup_directory = _local_sqlite_paths(settings)
        selected_backup_path = _safe_backup_path(backup_directory, backup_name)
        restored_from = _backup_response(selected_backup_path)
        if restored_from.integrity_status != "ok":
            raise BackupValidationError("Selected backup did not pass SQLite integrity validation.")

        safety_backup = create_data_backup(settings, backup_type="pre_restore")
        database_path.parent.mkdir(parents=True, exist_ok=True)
        restore_candidate = database_path.with_name(f".{database_path.name}.restore-{uuid4().hex}.tmp")
        engine = get_engine()
        engine.dispose()
        try:
            _write_sqlite_backup(selected_backup_path, restore_candidate)
            for suffix in ("-wal", "-shm"):
                database_path.with_name(f"{database_path.name}{suffix}").unlink(missing_ok=True)
            os.replace(restore_candidate, database_path)
            _read_database_metadata(database_path)
        finally:
            restore_candidate.unlink(missing_ok=True)
            engine.dispose()

        return RestoreDataBackupResponse(
            restored_from=restored_from,
            safety_backup=safety_backup,
            restored_at=datetime.now(timezone.utc),
            message="Local data restored. The app has reloaded the restored database.",
        )
