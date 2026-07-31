from fastapi import APIRouter, HTTPException, status

from app.config import get_settings
from app.schemas.data_safety import (
    DataBackupResponse,
    DataSafetyStatusResponse,
    RestoreDataBackupRequest,
    RestoreDataBackupResponse,
)
from app.services.data_safety import (
    BackupValidationError,
    DataSafetyUnavailableError,
    create_data_backup,
    get_data_safety_status,
    restore_data_backup,
)


router = APIRouter()


@router.get("", response_model=DataSafetyStatusResponse)
def get_data_safety() -> DataSafetyStatusResponse:
    return get_data_safety_status(get_settings())


@router.post("/backups", response_model=DataBackupResponse, status_code=status.HTTP_201_CREATED)
def post_data_backup() -> DataBackupResponse:
    try:
        return create_data_backup(get_settings())
    except DataSafetyUnavailableError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    except BackupValidationError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error


@router.post("/restore", response_model=RestoreDataBackupResponse)
def post_restore_data_backup(payload: RestoreDataBackupRequest) -> RestoreDataBackupResponse:
    try:
        return restore_data_backup(get_settings(), payload.backup_name)
    except DataSafetyUnavailableError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    except BackupValidationError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
