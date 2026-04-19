from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends

from app.config import get_settings
from app.db.session import get_db
from app.repositories.sqlalchemy import SqlAlchemySettingsRepository
from app.schemas.settings import AppSettingsResponse, ProviderMetadata, ProviderMetadataResponse
from app.services.provider_registry import build_provider_metadata
from app.services.settings import get_settings_payload, update_settings_payload
from app.schemas.settings import UpdateSettingsRequest

router = APIRouter()


@router.get("", response_model=AppSettingsResponse)
def get_app_settings(db: Session = Depends(get_db)) -> AppSettingsResponse:
    return get_settings_payload(SqlAlchemySettingsRepository(db), get_settings())


@router.patch("", response_model=AppSettingsResponse)
def patch_app_settings(payload: UpdateSettingsRequest, db: Session = Depends(get_db)) -> AppSettingsResponse:
    response = update_settings_payload(payload, SqlAlchemySettingsRepository(db), get_settings())
    db.commit()
    return response


@router.get("/providers", response_model=ProviderMetadataResponse)
def get_provider_metadata() -> ProviderMetadataResponse:
    providers = build_provider_metadata(get_settings())
    return ProviderMetadataResponse(
        providers=[ProviderMetadata.model_validate(provider.model_dump()) for provider in providers]
    )
