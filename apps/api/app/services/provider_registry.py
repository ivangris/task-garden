from pydantic import BaseModel

from app.config import Settings
from app.providers.ollama import OllamaExtractionProvider
from app.providers.recap_ollama import OllamaRecapNarrativeProvider
from app.providers.stubs import LocalOnlySyncProvider, LocalStubTaskExtractionProvider, MockRecapNarrativeProvider, RemoteApiSyncProvider
from app.providers.interfaces import RecapNarrativeProvider, SyncProvider, TaskExtractionProvider


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
            name="whisper_cpp",
            display_name="Local whisper.cpp",
            enabled=True,
            cloud=False,
            configured=bool(settings.stt_executable_path and settings.stt_model_path),
            selected=settings.stt_provider == "whisper_cpp",
        ),
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
            name="mock",
            display_name="Mock Extraction",
            enabled=True,
            cloud=False,
            configured=True,
            selected=settings.task_extraction_provider in {"mock", "local_stub"},
        ),
        ProviderMetadataRecord(
            kind="task_extraction",
            name="ollama",
            display_name="Local Ollama",
            enabled=True,
            cloud=False,
            configured=bool(settings.ollama_base_url and settings.extraction_model),
            selected=settings.task_extraction_provider == "ollama",
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
            kind="recap_narrative",
            name="off",
            display_name="Narrative Off",
            enabled=True,
            cloud=False,
            configured=True,
            selected=settings.recap_narrative_provider == "off",
        ),
        ProviderMetadataRecord(
            kind="recap_narrative",
            name="mock",
            display_name="Mock Recap Narrative",
            enabled=True,
            cloud=False,
            configured=True,
            selected=settings.recap_narrative_provider == "mock",
        ),
        ProviderMetadataRecord(
            kind="recap_narrative",
            name="ollama",
            display_name="Local Ollama Recap",
            enabled=True,
            cloud=False,
            configured=bool(settings.ollama_base_url and settings.recap_model),
            selected=settings.recap_narrative_provider == "ollama",
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
            configured=bool(settings.sync_base_url),
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


def build_task_extraction_provider(settings: Settings) -> TaskExtractionProvider:
    provider_name = settings.task_extraction_provider
    if provider_name in {"mock", "local_stub"}:
        return LocalStubTaskExtractionProvider()
    if provider_name == "ollama":
        return OllamaExtractionProvider(
            base_url=settings.ollama_base_url,
            model_name=settings.extraction_model,
            timeout_seconds=settings.extraction_timeout_seconds,
        )
    raise ValueError(f"Unsupported extraction provider: {provider_name}")


def build_recap_narrative_provider(settings: Settings) -> RecapNarrativeProvider:
    provider_name = settings.recap_narrative_provider
    if provider_name == "mock":
        return MockRecapNarrativeProvider()
    if provider_name == "ollama":
        return OllamaRecapNarrativeProvider(
            base_url=settings.ollama_base_url,
            model_name=settings.recap_model,
            timeout_seconds=settings.extraction_timeout_seconds,
        )
    raise ValueError(f"Unsupported recap narrative provider: {provider_name}")


def build_sync_provider(settings: Settings) -> SyncProvider:
    if settings.sync_provider == "local_only":
        return LocalOnlySyncProvider()
    if settings.sync_provider == "remote_api":
        return RemoteApiSyncProvider(settings.sync_base_url)
    raise ValueError(f"Unsupported sync provider: {settings.sync_provider}")
