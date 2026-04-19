from pydantic import BaseModel


class AppSettingsResponse(BaseModel):
    local_only_mode: bool
    cloud_enabled: bool
    stt_provider: str
    task_extraction_provider: str
    sync_provider: str
    auth_provider: str
    stt_model: str
    extraction_model: str
    sync_base_url: str | None = None


class UpdateSettingsRequest(BaseModel):
    local_only_mode: bool | None = None
    cloud_enabled: bool | None = None
    stt_provider: str | None = None
    task_extraction_provider: str | None = None
    sync_provider: str | None = None
    auth_provider: str | None = None
    stt_model: str | None = None
    extraction_model: str | None = None
    sync_base_url: str | None = None


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
