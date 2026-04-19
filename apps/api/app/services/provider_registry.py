from pydantic import BaseModel

from app.config import Settings


class ProviderMetadataRecord(BaseModel):
    kind: str
    name: str
    display_name: str
    enabled: bool
    cloud: bool
    configured: bool
    selected: bool


def build_provider_metadata(settings: Settings) -> list[ProviderMetadataRecord]:
    return [
        ProviderMetadataRecord(
            kind="stt",
            name="local_stub",
            display_name="Local STT Stub",
            enabled=True,
            cloud=False,
            configured=True,
            selected=settings.stt_provider == "local_stub",
        ),
        ProviderMetadataRecord(
            kind="stt",
            name="cloud_openai",
            display_name="Cloud STT Placeholder",
            enabled=not settings.local_only_mode and settings.cloud_enabled,
            cloud=True,
            configured=bool(settings.cloud_api_key),
            selected=settings.stt_provider == "cloud_openai",
        ),
        ProviderMetadataRecord(
            kind="task_extraction",
            name="local_stub",
            display_name="Local Extraction Stub",
            enabled=True,
            cloud=False,
            configured=True,
            selected=settings.task_extraction_provider == "local_stub",
        ),
        ProviderMetadataRecord(
            kind="task_extraction",
            name="cloud_openai",
            display_name="Cloud Extraction Placeholder",
            enabled=not settings.local_only_mode and settings.cloud_enabled,
            cloud=True,
            configured=bool(settings.cloud_api_key),
            selected=settings.task_extraction_provider == "cloud_openai",
        ),
        ProviderMetadataRecord(
            kind="sync",
            name="local_only",
            display_name="Local Only",
            enabled=True,
            cloud=False,
            configured=True,
            selected=settings.sync_provider == "local_only",
        ),
        ProviderMetadataRecord(
            kind="sync",
            name="remote_api",
            display_name="Remote Sync Placeholder",
            enabled=not settings.local_only_mode and settings.cloud_enabled,
            cloud=True,
            configured=False,
            selected=settings.sync_provider == "remote_api",
        ),
        ProviderMetadataRecord(
            kind="auth",
            name="none",
            display_name="No Auth",
            enabled=True,
            cloud=False,
            configured=True,
            selected=settings.auth_provider == "none",
        ),
        ProviderMetadataRecord(
            kind="auth",
            name="hosted_auth",
            display_name="Hosted Auth Placeholder",
            enabled=not settings.local_only_mode and settings.cloud_enabled,
            cloud=True,
            configured=False,
            selected=settings.auth_provider == "hosted_auth",
        ),
    ]

