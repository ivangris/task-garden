from app.providers.interfaces import (
    AuthProvider,
    AuthSession,
    ExtractionResult,
    STTProvider,
    SyncProvider,
    SyncResult,
    TaskExtractionProvider,
    TranscriptResult,
)


class LocalStubSTTProvider(STTProvider):
    name = "local_stub"

    def transcribe(self, audio_ref: str, options: dict | None = None) -> TranscriptResult:
        return TranscriptResult(
            text="",
            provider_name=self.name,
            model_name="whisper-local-placeholder",
            metadata={"audio_ref": audio_ref, "stub": True, "options": options or {}},
        )


class LocalStubTaskExtractionProvider(TaskExtractionProvider):
    name = "local_stub"

    def extract_tasks(
        self,
        raw_text: str,
        schema_version: str,
        prompt_version: str,
        context: dict | None = None,
    ) -> ExtractionResult:
        return ExtractionResult(
            provider_name=self.name,
            model_name="ollama-local-placeholder",
            schema_version=schema_version,
            prompt_version=prompt_version,
            summary="Phase 0 placeholder extraction result.",
            needs_review=True,
            open_questions=[],
            candidates=[],
        )


class LocalOnlySyncProvider(SyncProvider):
    name = "local_only"

    def sync(self, cursor: str | None = None) -> SyncResult:
        return SyncResult(status="disabled", message="Local-only mode is active.", metadata={"cursor": cursor})


class NoAuthProvider(AuthProvider):
    name = "none"

    def get_session(self) -> AuthSession:
        return AuthSession(status="disabled", provider_name=self.name)
