from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.config import get_settings
from app.db.session import get_db
from app.repositories.sqlalchemy import (
    SqlAlchemyChangeEventRepository,
    SqlAlchemyDeviceRepository,
    SqlAlchemyGardenStateRepository,
    SqlAlchemyProjectRepository,
    SqlAlchemyRawEntryRepository,
    SqlAlchemySettingsRepository,
    SqlAlchemySyncCursorRepository,
    SqlAlchemyTaskRepository,
)
from app.schemas.sync import (
    DeviceRegistrationRequest,
    DeviceResponse,
    SyncPullResponse,
    SyncPushRequest,
    SyncPushResponse,
    SyncStatusResponse,
)
from app.services.sync import get_sync_status, pull_changes, push_changes, register_device

router = APIRouter()


@router.get("", response_model=SyncStatusResponse)
def get_sync_status_route(
    device_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> SyncStatusResponse:
    return get_sync_status(
        device_id=device_id,
        settings=get_settings(),
        settings_repo=SqlAlchemySettingsRepository(db),
        devices=SqlAlchemyDeviceRepository(db),
        change_events=SqlAlchemyChangeEventRepository(db),
        cursors=SqlAlchemySyncCursorRepository(db),
    )


@router.post("/register-device", response_model=DeviceResponse)
def post_register_device(payload: DeviceRegistrationRequest, db: Session = Depends(get_db)) -> DeviceResponse:
    device = register_device(payload, SqlAlchemyDeviceRepository(db))
    db.commit()
    return DeviceResponse.model_validate(device)


@router.post("/push", response_model=SyncPushResponse)
def post_sync_push(payload: SyncPushRequest, db: Session = Depends(get_db)) -> SyncPushResponse:
    device_repo = SqlAlchemyDeviceRepository(db)
    if device_repo.get(payload.device_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not registered.")
    result = push_changes(
        device_id=payload.device_id,
        changes=payload.changes,
        change_events=SqlAlchemyChangeEventRepository(db),
        devices=device_repo,
        cursors=SqlAlchemySyncCursorRepository(db),
        tasks=SqlAlchemyTaskRepository(db),
        projects=SqlAlchemyProjectRepository(db),
        raw_entries=SqlAlchemyRawEntryRepository(db),
        settings_repo=SqlAlchemySettingsRepository(db),
        garden_states=SqlAlchemyGardenStateRepository(db),
        defaults=get_settings(),
    )
    db.commit()
    return result


@router.get("/pull", response_model=SyncPullResponse)
def get_sync_pull(
    device_id: str = Query(...),
    cursor: int | None = Query(default=None, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> SyncPullResponse:
    device_repo = SqlAlchemyDeviceRepository(db)
    if device_repo.get(device_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not registered.")
    result = pull_changes(
        device_id=device_id,
        cursor_value=cursor,
        limit=limit,
        change_events=SqlAlchemyChangeEventRepository(db),
        cursors=SqlAlchemySyncCursorRepository(db),
        devices=device_repo,
    )
    db.commit()
    return result
