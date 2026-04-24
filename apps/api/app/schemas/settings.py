from typing import Literal

from pydantic import BaseModel


class AppSettingsResponse(BaseModel):
    local_only_mode: bool
    cloud_enabled: bool
    stt_provider: str
    task_extraction_provider: str
    recap_narrative_provider: str
    sync_provider: str
    auth_provider: str
    stt_model: str
    extraction_model: str
    recap_model: str
    ollama_base_url: str
    extraction_timeout_seconds: int
    sync_base_url: str | None = None
    stt_executable_path: str | None = None
    stt_model_path: str | None = None
    stt_ready: bool = False


class UpdateSettingsRequest(BaseModel):
    local_only_mode: bool | None = None
    cloud_enabled: bool | None = None
    stt_provider: str | None = None
    task_extraction_provider: str | None = None
    recap_narrative_provider: str | None = None
    sync_provider: str | None = None
    auth_provider: str | None = None
    stt_model: str | None = None
    extraction_model: str | None = None
    recap_model: str | None = None
    ollama_base_url: str | None = None
    extraction_timeout_seconds: int | None = None
    sync_base_url: str | None = None
    stt_executable_path: str | None = None
    stt_model_path: str | None = None


class ProviderMetadata(BaseModel):
    kind: str
    name: str
    display_name: str
    enabled: bool
    cloud: bool
    configured: bool
    selected: bool


class ProviderMetadataResponse(BaseModel):
    providers: list[ProviderMetadata]


class ProviderCheckRequest(BaseModel):
    kind: Literal["task_extraction", "recap_narrative", "stt"]


class ProviderCheckResponse(BaseModel):
    kind: str
    provider_name: str
    ok: bool
    message: str
    model_name: str | None = None
    normalized_base_url: str | None = None
    details: dict[str, object] = {}


class LocalModelOption(BaseModel):
    name: str
    provider_name: str
    usable_for_chat: bool
    size: int | None = None
    modified_at: str | None = None


class LocalModelsResponse(BaseModel):
    ollama_base_url: str
    preferred_chat_model: str | None = None
    models: list[LocalModelOption]
