from app.config import Settings
from app.providers.ollama_common import normalize_ollama_base_url
from app.repositories.interfaces import SettingsRepository
from app.schemas.settings import AppSettingsResponse, UpdateSettingsRequest
from app.services.local_models import build_local_provider_defaults, discover_ollama_models, resolve_whisper_cpp_paths


SETTING_KEYS = (
    "local_only_mode",
    "cloud_enabled",
    "stt_provider",
    "task_extraction_provider",
    "recap_narrative_provider",
    "sync_provider",
    "auth_provider",
    "stt_model",
    "extraction_model",
    "recap_model",
    "ollama_base_url",
    "extraction_timeout_seconds",
    "sync_base_url",
    "stt_executable_path",
    "stt_model_path",
)


def get_settings_payload(settings_repo: SettingsRepository, defaults: Settings) -> AppSettingsResponse:
    stored = settings_repo.get_local_settings()
    discovered_models = discover_ollama_models(defaults) if defaults.auto_configure_local_defaults else []
    local_defaults = build_local_provider_defaults(defaults, discovered_models)

    extraction_provider = stored.get("task_extraction_provider", local_defaults.task_extraction_provider)
    if extraction_provider == "local_stub":
        extraction_provider = "mock"
    if "task_extraction_provider" not in stored and extraction_provider == "mock" and local_defaults.extraction_model:
        extraction_provider = "ollama"

    recap_provider = stored.get("recap_narrative_provider", local_defaults.recap_narrative_provider)
    if "recap_narrative_provider" not in stored and recap_provider in {"off", "mock"} and local_defaults.recap_model:
        recap_provider = "ollama"
    chat_model_names = {model.name for model in discovered_models if model.usable_for_chat}
    stored_extraction_model = stored.get("extraction_model")
    if isinstance(stored_extraction_model, str) and stored_extraction_model not in chat_model_names and local_defaults.extraction_model:
        stored_extraction_model = local_defaults.extraction_model
    stored_recap_model = stored.get("recap_model")
    if isinstance(stored_recap_model, str) and stored_recap_model not in chat_model_names and local_defaults.recap_model:
        stored_recap_model = local_defaults.recap_model

    stt_executable_path = stored.get("stt_executable_path", defaults.stt_executable_path)
    stt_model_path = stored.get("stt_model_path", defaults.stt_model_path)
    stt_executable_path, stt_model_path = resolve_whisper_cpp_paths(
        defaults.model_copy(update={"stt_executable_path": stt_executable_path, "stt_model_path": stt_model_path})
    )
    stt_defaults = defaults.model_copy(update={"stt_executable_path": stt_executable_path, "stt_model_path": stt_model_path})
    stt_local_defaults = build_local_provider_defaults(stt_defaults, discovered_models)
    default_stt_provider = defaults.stt_provider if defaults.stt_provider == "local_stub" else stt_local_defaults.stt_provider
    stored_stt_provider = stored.get("stt_provider", default_stt_provider)
    stt_provider = "local_stub" if stored_stt_provider == "local_stub" else "whisper_cpp"

    merged = {
        "local_only_mode": stored.get("local_only_mode", defaults.local_only_mode),
        "cloud_enabled": stored.get("cloud_enabled", defaults.cloud_enabled),
        "stt_provider": stt_provider,
        "task_extraction_provider": extraction_provider,
        "recap_narrative_provider": recap_provider,
        "sync_provider": stored.get("sync_provider", defaults.sync_provider),
        "auth_provider": stored.get("auth_provider", defaults.auth_provider),
        "stt_model": "" if stored.get("stt_model") == "whisper-local-placeholder" else stored.get("stt_model", stt_local_defaults.stt_model),
        "extraction_model": stored_extraction_model or local_defaults.extraction_model,
        "recap_model": stored_recap_model or local_defaults.recap_model,
        "ollama_base_url": normalize_ollama_base_url(stored.get("ollama_base_url", defaults.ollama_base_url)),
        "extraction_timeout_seconds": stored.get("extraction_timeout_seconds", defaults.extraction_timeout_seconds),
        "sync_base_url": stored.get("sync_base_url", defaults.sync_base_url),
        "stt_executable_path": stt_executable_path,
        "stt_model_path": stt_model_path,
        "stt_ready": stt_local_defaults.stt_ready,
    }
    return AppSettingsResponse(**merged)


def update_settings_payload(
    payload: UpdateSettingsRequest,
    settings_repo: SettingsRepository,
    defaults: Settings,
) -> AppSettingsResponse:
    values = payload.model_dump(exclude_unset=True)
    filtered = {key: value for key, value in values.items() if key in SETTING_KEYS}
    if filtered.get("task_extraction_provider") == "local_stub":
        filtered["task_extraction_provider"] = "mock"
    if "ollama_base_url" in filtered and filtered["ollama_base_url"] is not None:
        filtered["ollama_base_url"] = normalize_ollama_base_url(filtered["ollama_base_url"])
    if filtered:
        settings_repo.save_local_settings(filtered)
    return get_settings_payload(settings_repo, defaults)
