from app.providers.interfaces import (
    AuthProvider,
    AuthSession,
    ExtractionResult,
    RecapNarrativeProvider,
    RecapNarrativeResult,
    STTProvider,
    SyncProvider,
    SyncResult,
    TaskExtractionProvider,
    TranscriptResult,
)
from app.services.extractions import DeterministicMockExtractionProvider


class LocalStubSTTProvider(STTProvider):
    name = "local_stub"

    def transcribe(self, audio_ref: str, options: dict | None = None) -> TranscriptResult:
        provided_seed = (options or {}).get("seed_text")
        if isinstance(provided_seed, str) and provided_seed.strip():
            transcript = provided_seed.strip()
        else:
            transcript = "Follow up with the vendor, draft the Atlas update, and plan tomorrow's priorities."
        return TranscriptResult(
            text=transcript,
            provider_name=self.name,
            model_name="deterministic-local-stub",
            metadata={"audio_ref": audio_ref, "stub": True, "options": options or {}},
        )


class LocalStubTaskExtractionProvider(TaskExtractionProvider):
    name = "mock"

    def extract_tasks(
        self,
        raw_text: str,
        schema_version: str,
        prompt_version: str,
        context: dict | None = None,
    ) -> ExtractionResult:
        provider = DeterministicMockExtractionProvider()
        return provider.extract_tasks(raw_text, schema_version, prompt_version, context)


class MockRecapNarrativeProvider(RecapNarrativeProvider):
    name = "mock"

    def generate_narrative(
        self,
        summary: dict,
        prompt_version: str,
    ) -> RecapNarrativeResult:
        period_label = summary.get("period_label", "This period")
        headline_metrics = summary.get("headline_metrics", {})
        top_projects = summary.get("top_projects", [])
        garden = summary.get("garden_summary", {})
        project_text = ", ".join(item.get("project_name", "Independent") for item in top_projects[:2]) or "independent work"
        text = (
            f"{period_label} stayed concrete. You finished {headline_metrics.get('total_tasks_completed', 0)} tasks "
            f"across {headline_metrics.get('active_days', 0)} active days. "
            f"The period leaned most toward {project_text}, while the garden moved "
            f"{garden.get('stage_change_label', 'forward')} with {garden.get('xp_gained', 0)} XP gained."
        )
        return RecapNarrativeResult(
            narrative_text=text,
            provider_name=self.name,
            model_name="deterministic-mock-recap",
            prompt_version=prompt_version,
            metadata={"stub": True},
        )


class LocalOnlySyncProvider(SyncProvider):
    name = "local_only"

    def sync(self, cursor: str | None = None) -> SyncResult:
        return SyncResult(status="disabled", message="Local-only mode is active.", metadata={"cursor": cursor})


class RemoteApiSyncProvider(SyncProvider):
    name = "remote_api"

    def __init__(self, base_url: str | None) -> None:
        self.base_url = base_url

    def sync(self, cursor: str | None = None) -> SyncResult:
        return SyncResult(
            status="ready",
            message="Remote sync provider is configured as a placeholder.",
            metadata={"cursor": cursor, "base_url": self.base_url},
        )


class NoAuthProvider(AuthProvider):
    name = "none"

    def get_session(self) -> AuthSession:
        return AuthSession(status="disabled", provider_name=self.name)
