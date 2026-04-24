from __future__ import annotations

import hashlib
import json

from app.config import Settings
from app.domain.entities import RecapNarrative
from app.providers.extraction_common import ExtractionProviderError
from app.providers.recap_ollama import OLLAMA_RECAP_PROMPT_VERSION
from app.repositories.interfaces import RecapNarrativeRepository
from app.schemas.recaps import RecapNarrativeResponse, RecapPeriodResponse
from app.services.common import generate_id, utcnow
from app.services.provider_registry import build_recap_narrative_provider


RECAP_SUMMARY_VERSION = "1.0"


def build_recap_narrative_summary(recap: RecapPeriodResponse) -> dict[str, object]:
    metrics = {item.metric_key: item for item in recap.metrics}
    top_projects = [
        {
            "project_name": item.project_name,
            "completed_task_count": item.completed_task_count,
            "xp_gained": item.xp_gained,
        }
        for item in recap.project_summaries[:3]
    ]
    highlights = [
        {
            "card_type": item.card_type,
            "title": item.title,
            "subtitle": item.subtitle,
            "primary_value": item.primary_value,
            "secondary_value": item.secondary_value,
        }
        for item in recap.cards[:4]
    ]
    milestones = [
        {"title": item.title, "metric_value": item.metric_value}
        for item in recap.milestones[:3]
    ]
    return {
        "summary_version": RECAP_SUMMARY_VERSION,
        "period_type": recap.period_type,
        "period_label": recap.period_label,
        "window_start": recap.window_start.isoformat(),
        "window_end": recap.window_end.isoformat(),
        "headline_metrics": {
            "total_tasks_completed": metrics.get("total_tasks_completed").numeric_value if metrics.get("total_tasks_completed") else 0,
            "active_days": metrics.get("active_days").numeric_value if metrics.get("active_days") else 0,
            "completion_rate": metrics.get("completion_rate").numeric_value if metrics.get("completion_rate") else None,
            "xp_gained": metrics.get("xp_gained").numeric_value if metrics.get("xp_gained") else 0,
            "unlocks_earned": metrics.get("unlocks_earned").numeric_value if metrics.get("unlocks_earned") else 0,
            "overdue_recovered_count": metrics.get("overdue_recovered_count").numeric_value if metrics.get("overdue_recovered_count") else 0,
        },
        "top_projects": top_projects,
        "highlights": highlights,
        "milestones": milestones,
        "streak_summary": recap.streak_summary.model_dump(mode="json") if recap.streak_summary is not None else None,
        "garden_summary": {
            "stage_change": metrics.get("garden_stage_change").text_value if metrics.get("garden_stage_change") else None,
            "stage_change_label": (
                (metrics.get("garden_stage_change").text_value or "").replace("->", " to ").replace("_", " ")
                if metrics.get("garden_stage_change")
                else None
            ),
            "health_delta": metrics.get("garden_health_delta").numeric_value if metrics.get("garden_health_delta") else 0,
            "xp_gained": metrics.get("xp_gained").numeric_value if metrics.get("xp_gained") else 0,
            "unlocks_earned": metrics.get("unlocks_earned").numeric_value if metrics.get("unlocks_earned") else 0,
        },
        "representative_task_titles": [
            title
            for title in [metrics.get("biggest_completed_task").text_value if metrics.get("biggest_completed_task") else None]
            if title
        ],
    }


def recap_summary_hash(summary: dict[str, object]) -> str:
    compact = json.dumps(summary, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(compact.encode("utf-8")).hexdigest()


def get_recap_narrative(
    period_id: str,
    repository: RecapNarrativeRepository,
) -> RecapNarrativeResponse:
    narrative = repository.get_for_period(period_id)
    if narrative is None:
        return RecapNarrativeResponse(period_id=period_id, generation_status="not_generated")
    return RecapNarrativeResponse.model_validate(narrative)


def generate_recap_narrative(
    recap: RecapPeriodResponse,
    repository: RecapNarrativeRepository,
    settings: Settings,
) -> RecapNarrativeResponse:
    summary = build_recap_narrative_summary(recap)
    summary_hash = recap_summary_hash(summary)
    now = utcnow()
    provider_name = settings.recap_narrative_provider

    if provider_name == "off":
        saved = repository.upsert_for_period(
            RecapNarrative(
                id=generate_id(),
                period_id=recap.id,
                generation_status="disabled",
                provider_name="off",
                model_name="",
                prompt_version=OLLAMA_RECAP_PROMPT_VERSION,
                source_summary_version=RECAP_SUMMARY_VERSION,
                source_summary_hash=summary_hash,
                generated_at=now,
                narrative_text=None,
                error_metadata={"reason": "provider_off", "message": "Recap narrative generation is disabled in settings."},
            )
        )
        return RecapNarrativeResponse.model_validate(saved)

    try:
        provider = build_recap_narrative_provider(settings)
        result = provider.generate_narrative(summary, OLLAMA_RECAP_PROMPT_VERSION)
        saved = repository.upsert_for_period(
            RecapNarrative(
                id=generate_id(),
                period_id=recap.id,
                generation_status="generated",
                provider_name=result.provider_name,
                model_name=result.model_name,
                prompt_version=result.prompt_version,
                source_summary_version=RECAP_SUMMARY_VERSION,
                source_summary_hash=summary_hash,
                generated_at=now,
                narrative_text=result.narrative_text,
                error_metadata=result.metadata,
            )
        )
    except ExtractionProviderError as exc:
        saved = repository.upsert_for_period(
            RecapNarrative(
                id=generate_id(),
                period_id=recap.id,
                generation_status="failed",
                provider_name=provider_name,
                model_name=settings.recap_model if provider_name == "ollama" else "deterministic-mock-recap",
                prompt_version=OLLAMA_RECAP_PROMPT_VERSION,
                source_summary_version=RECAP_SUMMARY_VERSION,
                source_summary_hash=summary_hash,
                generated_at=now,
                narrative_text=None,
                error_metadata={"reason": exc.reason, "message": exc.message},
            )
        )
    return RecapNarrativeResponse.model_validate(saved)
