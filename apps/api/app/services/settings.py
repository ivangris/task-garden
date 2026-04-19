from app.config import Settings
from app.repositories.interfaces import SettingsRepository
from app.schemas.settings import AppSettingsResponse, UpdateSettingsRequest


SETTING_KEYS = (
    "local_only_mode",
    "cloud_enabled",
    "stt_provider",
    "task_extraction_provider",
    "sync_provider",
    "auth_provider",
    "stt_model",
    "extraction_model",
    "sync_base_url",
)


def get_settings_payload(settings_repo: SettingsRepository, defaults: Settings) -> AppSettingsResponse:
    stored = settings_repo.get_local_settings()
    merged = {
        "local_only_mode": stored.get("local_only_mode", defaults.local_only_mode),
        "cloud_enabled": stored.get("cloud_enabled", defaults.cloud_enabled),
        "stt_provider": stored.get("stt_provider", defaults.stt_provider),
        "task_extraction_provider": stored.get("task_extraction_provider", defaults.task_extraction_provider),
        "sync_provider": stored.get("sync_provider", defaults.sync_provider),
        "auth_provider": stored.get("auth_provider", defaults.auth_provider),
        "stt_model": stored.get("stt_model", defaults.stt_model),
        "extraction_model": stored.get("extraction_model", defaults.extraction_model),
        "sync_base_url": stored.get("sync_base_url", defaults.sync_base_url),
    }
    return AppSettingsResponse(**merged)


def update_settings_payload(
    payload: UpdateSettingsRequest,
    settings_repo: SettingsRepository,
    defaults: Settings,
) -> AppSettingsResponse:
    values = payload.model_dump(exclude_unset=True)
    filtered = {key: value for key, value in values.items() if key in SETTING_KEYS}
    if filtered:
        settings_repo.save_local_settings(filtered)
    return get_settings_payload(settings_repo, defaults)
