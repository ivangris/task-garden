from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(slots=True)
class TranscriptSegmentResult:
    segment_index: int
    text: str
    start_ms: int | None = None
    end_ms: int | None = None
    speaker_label: str | None = None


@dataclass(slots=True)
class TranscriptResult:
    text: str
    segments: list[TranscriptSegmentResult] = field(default_factory=list)
    provider_name: str = ""
    model_name: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ExtractedTaskCandidateResult:
    title: str
    details: str | None = None
    project_or_group: str | None = None
    priority: str = "medium"
    effort: str = "medium"
    energy: str = "medium"
    labels: list[str] = field(default_factory=list)
    due_date: str | None = None
    parent_task_title: str | None = None
    confidence: float = 0.0
    source_excerpt: str | None = None


@dataclass(slots=True)
class ExtractionResult:
    provider_name: str
    model_name: str
    schema_version: str
    prompt_version: str
    summary: str | None = None
    needs_review: bool = True
    open_questions: list[str] = field(default_factory=list)
    candidates: list[ExtractedTaskCandidateResult] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SyncResult:
    status: str
    message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RecapNarrativeResult:
    narrative_text: str
    provider_name: str
    model_name: str
    prompt_version: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AuthSession:
    status: str
    provider_name: str
    user_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class STTProvider(Protocol):
    name: str

    def transcribe(self, audio_ref: str, options: dict[str, Any] | None = None) -> TranscriptResult: ...


class TaskExtractionProvider(Protocol):
    name: str

    def extract_tasks(
        self,
        raw_text: str,
        schema_version: str,
        prompt_version: str,
        context: dict[str, Any] | None = None,
    ) -> ExtractionResult: ...


class RecapNarrativeProvider(Protocol):
    name: str

    def generate_narrative(
        self,
        summary: dict[str, Any],
        prompt_version: str,
    ) -> RecapNarrativeResult: ...


class SyncProvider(Protocol):
    name: str

    def sync(self, cursor: str | None = None) -> SyncResult: ...


class AuthProvider(Protocol):
    name: str

    def get_session(self) -> AuthSession: ...
