from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends

from app.config import get_settings
from app.db.session import get_db
from app.repositories.sqlalchemy import SqlAlchemyChangeEventRepository, SqlAlchemySettingsRepository
from app.schemas.settings import (
    AppSettingsResponse,
    LocalModelOption,
    LocalModelsResponse,
    ProviderCheckRequest,
    ProviderCheckResponse,
    ProviderMetadata,
    ProviderMetadataResponse,
)
from app.services.provider_registry import build_provider_metadata
from app.services.provider_checks import check_provider
from app.services.local_models import discover_ollama_models, normalized_ollama_base_url, select_preferred_chat_model
from app.services.settings import get_settings_payload, update_settings_payload
from app.schemas.settings import UpdateSettingsRequest
from app.services.sync import record_change_event, snapshot_settings
from fastapi import Header

router = APIRouter()


@router.get("", response_model=AppSettingsResponse)
def get_app_settings(db: Session = Depends(get_db)) -> AppSettingsResponse:
    return get_settings_payload(SqlAlchemySettingsRepository(db), get_settings())


@router.patch("", response_model=AppSettingsResponse)
def patch_app_settings(
    payload: UpdateSettingsRequest,
    db: Session = Depends(get_db),
    device_id: str | None = Header(default=None, alias="X-Task-Garden-Device-Id"),
) -> AppSettingsResponse:
    response = update_settings_payload(payload, SqlAlchemySettingsRepository(db), get_settings())
    record_change_event(
        SqlAlchemyChangeEventRepository(db),
        entity_type="settings",
        entity_id="local_settings",
        change_type="updated",
        payload=snapshot_settings(response),
        device_id=device_id,
    )
    db.commit()
    return response


@router.get("/providers", response_model=ProviderMetadataResponse)
def get_provider_metadata(db: Session = Depends(get_db)) -> ProviderMetadataResponse:
    defaults = get_settings()
    effective_settings = defaults.model_copy(
        update=get_settings_payload(SqlAlchemySettingsRepository(db), defaults).model_dump(exclude={"stt_ready"})
    )
    providers = build_provider_metadata(effective_settings)
    return ProviderMetadataResponse(
        providers=[ProviderMetadata.model_validate(provider.model_dump()) for provider in providers]
    )


@router.post("/providers/check", response_model=ProviderCheckResponse)
def post_provider_check(payload: ProviderCheckRequest, db: Session = Depends(get_db)) -> ProviderCheckResponse:
    defaults = get_settings()
    effective_settings = defaults.model_copy(
        update=get_settings_payload(SqlAlchemySettingsRepository(db), defaults).model_dump(exclude={"stt_ready"})
    )
    return check_provider(effective_settings, payload.kind)


@router.get("/local-models", response_model=LocalModelsResponse)
def get_local_models(db: Session = Depends(get_db)) -> LocalModelsResponse:
    defaults = get_settings()
    effective_settings = defaults.model_copy(
        update=get_settings_payload(SqlAlchemySettingsRepository(db), defaults).model_dump(exclude={"stt_ready"})
    )
    models = discover_ollama_models(effective_settings)
    return LocalModelsResponse(
        ollama_base_url=normalized_ollama_base_url(effective_settings),
        preferred_chat_model=select_preferred_chat_model([model.name for model in models]),
        models=[LocalModelOption(**model.__dict__) for model in models],
    )
