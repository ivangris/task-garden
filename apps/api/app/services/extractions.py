from datetime import datetime
import re
from typing import Iterable

from fastapi import HTTPException, status

from app.domain.entities import ExtractedTaskCandidate, ExtractionBatch, RawEntry
from app.providers.extraction_common import ExtractionProviderError
from app.providers.interfaces import ExtractedTaskCandidateResult, ExtractionResult, TaskExtractionProvider
from app.repositories.interfaces import (
    ActivityEventRepository,
    ExtractedTaskCandidateRepository,
    ExtractionBatchRepository,
    ProjectRepository,
    RawEntryRepository,
    TaskRepository,
)
from app.schemas.tasks import CreateTaskRequest
from app.schemas.extractions import ConfirmExtractionRequest
from app.services.activity import log_activity
from app.services.common import generate_id, utcnow
from app.services.tasks import create_task


TEMPORAL_SIGNALS = (
    "today",
    "tomorrow",
    "this week",
    "next week",
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
)


def _parse_due_date(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _normalize_whitespace(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = re.sub(r"\s+", " ", value).strip()
    return cleaned or None


def _normalize_title(value: str) -> str:
    cleaned = re.sub(r"^[\-\*\d\.\)\s]+", "", value).strip(" .,:;-")
    cleaned = re.sub(r"\s+", " ", cleaned)
    if not cleaned:
        return value.strip()
    return cleaned[:1].upper() + cleaned[1:]


def _normalize_labels(labels: list[str]) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []
    for label in labels:
        cleaned = re.sub(r"\s+", " ", label.strip().lower())
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            normalized.append(cleaned)
    return normalized


def _has_temporal_signal(raw_text: str, excerpt: str | None) -> bool:
    haystack = f"{raw_text} {excerpt or ''}".lower()
    if any(token in haystack for token in TEMPORAL_SIGNALS):
        return True
    return bool(re.search(r"\b\d{4}-\d{2}-\d{2}\b", haystack))


def _normalize_provider_candidate(raw_text: str, candidate: ExtractedTaskCandidateResult) -> ExtractedTaskCandidateResult:
    title = _normalize_title(candidate.title)
    details = _normalize_whitespace(candidate.details)
    project_or_group = _normalize_whitespace(candidate.project_or_group)
    parent_task_title = _normalize_whitespace(candidate.parent_task_title)
    source_excerpt = _normalize_whitespace(candidate.source_excerpt) or _normalize_whitespace(raw_text[:180])
    due_date = candidate.due_date if _has_temporal_signal(raw_text, source_excerpt) else None
    confidence = max(0.0, min(1.0, candidate.confidence))

    # Keep obviously low-signal labels out of the review surface.
    labels = [label for label in _normalize_labels(candidate.labels) if label not in {"task", "todo", "general"}]

    if priority := candidate.priority:
        priority = priority.lower()
    else:
        priority = "medium"
    if effort := candidate.effort:
        effort = effort.lower()
    else:
        effort = "medium"
    if energy := candidate.energy:
        energy = energy.lower()
    else:
        energy = "medium"

    return ExtractedTaskCandidateResult(
        title=title,
        details=details,
        project_or_group=project_or_group,
        priority=priority,
        effort=effort,
        energy=energy,
        labels=labels,
        due_date=due_date,
        parent_task_title=parent_task_title,
        confidence=confidence,
        source_excerpt=source_excerpt,
    )


def _candidate_from_result(extraction_id: str, candidate: ExtractedTaskCandidateResult) -> ExtractedTaskCandidate:
    return ExtractedTaskCandidate(
        id=generate_id(),
        extraction_batch_id=extraction_id,
        title=candidate.title,
        details=candidate.details,
        project_or_group=candidate.project_or_group,
        priority=candidate.priority,
        effort=candidate.effort,
        energy=candidate.energy,
        labels=list(candidate.labels),
        due_date=candidate.due_date,
        parent_task_title=candidate.parent_task_title,
        confidence=max(0.0, min(1.0, candidate.confidence)),
        source_excerpt=candidate.source_excerpt,
        candidate_status="pending_review",
    )


def _extraction_error_detail(provider_name: str, reason: str, message: str) -> str:
    if reason == "provider_unavailable":
        return (
            f"Task extraction could not reach {provider_name}. {message} "
            "Your saved entry is still here, and you can retry after checking the local provider setup."
        )
    if reason == "provider_timeout":
        return (
            f"Task extraction timed out in {provider_name}. {message} "
            "Your entry is still saved, so you can retry without losing anything."
        )
    if reason == "malformed_output":
        return (
            f"{provider_name} returned a response that could not be reviewed safely. {message} "
            "Try again, or switch providers in Settings."
        )
    if reason in {"empty_response", "low_signal_response"}:
        return (
            f"{provider_name} did not produce enough usable structure this time. {message} "
            "You can retry, edit the raw note, or add tasks manually."
        )
    return f"Extraction failed with provider '{provider_name}' ({reason}): {message}"


def _candidate_changed(original: ExtractedTaskCandidate, reviewed: ExtractedTaskCandidate) -> bool:
    return any(
        getattr(original, field) != getattr(reviewed, field)
        for field in (
            "title",
            "details",
            "project_or_group",
            "priority",
            "effort",
            "energy",
            "labels",
            "due_date",
            "parent_task_title",
            "confidence",
            "source_excerpt",
        )
    )


class DeterministicMockExtractionProvider(TaskExtractionProvider):
    name = "mock"

    def extract_tasks(
        self,
        raw_text: str,
        schema_version: str,
        prompt_version: str,
        context: dict | None = None,
    ) -> ExtractionResult:
        normalized = raw_text.replace("\r", "\n")
        segments = [part.strip(" -\t") for part in normalized.replace(";", "\n").split("\n") if part.strip()]
        if not segments:
            segments = [raw_text.strip()]

        candidate_texts: list[str] = []
        for segment in segments:
            pieces = [piece.strip() for piece in segment.split(" and ") if piece.strip()]
            candidate_texts.extend(pieces if len(pieces) <= 2 else [segment])

        candidates = [self._build_candidate(text, index) for index, text in enumerate(candidate_texts[:4], start=1)]
        summary = f"{len(candidates)} possible task candidates extracted from the raw entry."
        open_questions = []
        if any(candidate.project_or_group is None for candidate in candidates):
            open_questions.append("One or more tasks may need a project assignment.")
        return ExtractionResult(
            provider_name=self.name,
            model_name="task-garden-mock-v1",
            schema_version=schema_version,
            prompt_version=prompt_version,
            summary=summary,
            needs_review=True,
            open_questions=open_questions,
            candidates=candidates,
        )

    def _build_candidate(self, text: str, index: int) -> ExtractedTaskCandidateResult:
        lower = text.lower()
        project = None
        if "project " in lower:
            project = text[lower.index("project ") + len("project ") :].split(" ")[0].strip(" :.,")
        elif "for " in lower:
            project = text[lower.index("for ") + len("for ") :].split(" ")[0].strip(" :.,")

        priority = "high" if any(word in lower for word in ("urgent", "asap", "important")) else "medium"
        effort = "small" if any(word in lower for word in ("email", "call", "reply", "book")) else "large" if any(word in lower for word in ("build", "prepare", "draft", "plan")) else "medium"
        energy = "high" if any(word in lower for word in ("deep", "write", "design", "build")) else "low" if any(word in lower for word in ("call", "email", "book")) else "medium"
        labels = []
        if "follow up" in lower or "follow-up" in lower:
            labels.append("follow-up")
        if "admin" in lower:
            labels.append("admin")
        if "today" in lower:
            due_date = utcnow().isoformat()
        elif "tomorrow" in lower:
            due_date = utcnow().replace(hour=17, minute=0, second=0, microsecond=0)
            due_date = due_date.isoformat()
        elif "this week" in lower:
            due_date = utcnow().isoformat()
        else:
            due_date = None

        cleaned = text.rstrip(".")
        title = cleaned[:1].upper() + cleaned[1:]
        details = f"Mock extraction inferred this from the entry: {cleaned}" if len(cleaned) < 100 else cleaned
        excerpt = text[:180]
        confidence = max(0.56, min(0.88, 0.78 - (index * 0.06)))
        return ExtractedTaskCandidateResult(
            title=title,
            details=details,
            project_or_group=project,
            priority=priority,
            effort=effort,
            energy=energy,
            labels=labels,
            due_date=due_date,
            parent_task_title=None,
            confidence=confidence,
            source_excerpt=excerpt,
        )


def run_extraction_for_entry(
    entry_id: str,
    raw_entries: RawEntryRepository,
    extraction_batches: ExtractionBatchRepository,
    candidates_repo: ExtractedTaskCandidateRepository,
    activity_events: ActivityEventRepository,
    provider: TaskExtractionProvider,
    *,
    schema_version: str,
    prompt_version: str,
) -> tuple[ExtractionBatch, list[ExtractedTaskCandidate]]:
    entry = raw_entries.get(entry_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Raw entry not found.")

    try:
        provider_result = provider.extract_tasks(entry.raw_text, schema_version=schema_version, prompt_version=prompt_version)
    except ExtractionProviderError as exc:
        log_activity(
            activity_events,
            event_type="extraction_failed",
            entity_type="raw_entry",
            entity_id=entry.id,
            metadata={"provider_name": provider.name, "reason": exc.reason, "message": exc.message},
            device_id=entry.device_id,
        )
        status_code = {
            "provider_unavailable": status.HTTP_503_SERVICE_UNAVAILABLE,
            "provider_timeout": status.HTTP_504_GATEWAY_TIMEOUT,
            "malformed_output": status.HTTP_502_BAD_GATEWAY,
            "empty_response": status.HTTP_502_BAD_GATEWAY,
            "low_signal_response": status.HTTP_422_UNPROCESSABLE_CONTENT,
        }.get(exc.reason, status.HTTP_502_BAD_GATEWAY)
        raise HTTPException(
            status_code=status_code,
            detail=_extraction_error_detail(provider.name, exc.reason, exc.message),
        ) from exc
    except Exception as exc:  # noqa: BLE001
        log_activity(
            activity_events,
            event_type="extraction_failed",
            entity_type="raw_entry",
            entity_id=entry.id,
            metadata={"provider_name": provider.name, "reason": "unexpected_error", "message": str(exc)},
            device_id=entry.device_id,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Task extraction failed unexpectedly in {provider.name}: {exc}",
        ) from exc
    normalized_candidates = [_normalize_provider_candidate(entry.raw_text, candidate) for candidate in provider_result.candidates]
    if not normalized_candidates and not provider_result.open_questions:
        log_activity(
            activity_events,
            event_type="extraction_failed",
            entity_type="raw_entry",
            entity_id=entry.id,
            metadata={"provider_name": provider.name, "reason": "low_signal_response", "message": "No reviewable task candidates were produced."},
            device_id=entry.device_id,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=_extraction_error_detail(
                provider.name,
                "low_signal_response",
                "No reviewable task candidates were produced.",
            ),
        )
    batch = ExtractionBatch(
        id=generate_id(),
        raw_entry_id=entry.id,
        provider_name=provider_result.provider_name,
        model_name=provider_result.model_name,
        schema_version=provider_result.schema_version,
        prompt_version=provider_result.prompt_version,
        summary=provider_result.summary,
        needs_review=provider_result.needs_review,
        open_questions=provider_result.open_questions,
        created_at=utcnow(),
    )
    created_batch = extraction_batches.add(batch)
    created_candidates = candidates_repo.add_many(
        [_candidate_from_result(created_batch.id, candidate) for candidate in normalized_candidates]
    )

    entry.entry_status = "extracted"
    entry.updated_at = utcnow()
    raw_entries.update(entry)
    log_activity(
        activity_events,
        event_type="extraction_completed",
        entity_type="extraction_batch",
        entity_id=created_batch.id,
        metadata={
            "raw_entry_id": entry.id,
            "candidate_count": len(created_candidates),
            "provider_name": provider_result.provider_name,
            "model_name": provider_result.model_name,
            "provider_metadata": provider_result.metadata,
        },
        device_id=entry.device_id,
    )
    return created_batch, created_candidates


def get_extraction(
    extraction_id: str,
    extraction_batches: ExtractionBatchRepository,
    candidates_repo: ExtractedTaskCandidateRepository,
) -> tuple[ExtractionBatch, list[ExtractedTaskCandidate]]:
    batch = extraction_batches.get(extraction_id)
    if batch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Extraction batch not found.")
    return batch, candidates_repo.list_for_extraction(extraction_id)


def confirm_extraction(
    extraction_id: str,
    payload: ConfirmExtractionRequest,
    extraction_batches: ExtractionBatchRepository,
    candidates_repo: ExtractedTaskCandidateRepository,
    raw_entries: RawEntryRepository,
    tasks: TaskRepository,
    projects: ProjectRepository,
    activity_events: ActivityEventRepository,
) -> tuple[list[str], list[ExtractedTaskCandidate]]:
    batch, existing_candidates = get_extraction(extraction_id, extraction_batches, candidates_repo)
    if not batch.needs_review:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This extraction has already been confirmed.")

    raw_entry = raw_entries.get(batch.raw_entry_id)
    if raw_entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Raw entry not found.")

    candidate_map = {candidate.id: candidate for candidate in existing_candidates}
    reviewed_ids = {candidate.id for candidate in payload.candidates}
    existing_ids = set(candidate_map.keys())
    if reviewed_ids != existing_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="All extraction candidates must be reviewed before confirmation.",
        )
    reviewed_candidates: list[ExtractedTaskCandidate] = []
    created_task_ids: list[str] = []

    for reviewed in payload.candidates:
        original = candidate_map.get(reviewed.id)
        if original is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Candidate does not belong to this extraction.")

        updated = ExtractedTaskCandidate(
            id=original.id,
            extraction_batch_id=original.extraction_batch_id,
            title=reviewed.title.strip(),
            details=reviewed.details.strip() if reviewed.details else None,
            project_or_group=reviewed.project_or_group.strip() if reviewed.project_or_group else None,
            priority=reviewed.priority,
            effort=reviewed.effort,
            energy=reviewed.energy,
            labels=reviewed.labels,
            due_date=reviewed.due_date,
            parent_task_title=reviewed.parent_task_title.strip() if reviewed.parent_task_title else None,
            confidence=reviewed.confidence,
            source_excerpt=reviewed.source_excerpt.strip() if reviewed.source_excerpt else original.source_excerpt,
            candidate_status="pending_review",
        )

        changed = _candidate_changed(original, updated)
        if reviewed.decision == "rejected":
            updated.candidate_status = "rejected"
            log_activity(
                activity_events,
                event_type="task_rejected",
                entity_type="extracted_task_candidate",
                entity_id=updated.id,
                metadata={"extraction_id": extraction_id},
                device_id=raw_entry.device_id,
            )
        else:
            updated.candidate_status = "edited" if changed else "accepted"
            matched_project_id = None
            if updated.project_or_group:
                matched_project = next(
                    (project for project in projects.list_all() if project.name.lower() == updated.project_or_group.lower()),
                    None,
                )
                matched_project_id = matched_project.id if matched_project else None
            created_task = create_task(
                payload=CreateTaskRequest(
                    title=updated.title,
                    details=updated.details,
                    project_id=matched_project_id,
                    status="inbox",
                    priority=updated.priority,
                    effort=updated.effort,
                    energy=updated.energy,
                    due_date=_parse_due_date(updated.due_date),
                    source_raw_entry_id=raw_entry.id,
                    device_id=raw_entry.device_id,
                ),
                tasks=tasks,
                projects=projects,
                activity_events=activity_events,
            )
            created_task.source_extraction_batch_id = extraction_id
            tasks.update(created_task)
            created_task_ids.append(created_task.id)
            log_activity(
                activity_events,
                event_type="task_confirmed",
                entity_type="extracted_task_candidate",
                entity_id=updated.id,
                metadata={"task_id": created_task.id},
                device_id=raw_entry.device_id,
            )
            log_activity(
                activity_events,
                event_type="task_confirmed_from_extraction",
                entity_type="task",
                entity_id=created_task.id,
                metadata={"candidate_id": updated.id, "extraction_id": extraction_id},
                device_id=raw_entry.device_id,
            )

        reviewed_candidates.append(updated)

    updated_candidates = candidates_repo.update_many(reviewed_candidates)
    batch.needs_review = False
    extraction_batches.update(batch)
    raw_entry.entry_status = "reviewed"
    raw_entry.updated_at = utcnow()
    raw_entries.update(raw_entry)
    return created_task_ids, updated_candidates
