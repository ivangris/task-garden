from __future__ import annotations

from typing import Any

import httpx

from app.config import Settings
from app.services.local_models import whisper_cpp_is_ready
from app.providers.ollama_common import build_ollama_tags_url, normalize_ollama_base_url, ollama_base_url_help_text
from app.schemas.settings import ProviderCheckResponse


def _extract_model_names(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return []
    models = payload.get("models")
    if not isinstance(models, list):
        return []
    names: list[str] = []
    for item in models:
        if isinstance(item, dict):
            name = item.get("name")
            if isinstance(name, str) and name.strip():
                names.append(name.strip())
    return names


def check_provider(settings: Settings, kind: str) -> ProviderCheckResponse:
    if kind == "stt":
        if settings.stt_provider == "local_stub":
            return ProviderCheckResponse(
                kind=kind,
                provider_name="local_stub",
                ok=True,
                model_name="deterministic-local-stub",
                message="Testing transcription mode is selected. It does not create real transcripts.",
                details={"reason": "testing_mode"},
            )
        ready = whisper_cpp_is_ready(settings)
        return ProviderCheckResponse(
            kind=kind,
            provider_name="whisper_cpp",
            ok=ready,
            model_name=settings.stt_model or None,
            message=(
                "Local transcription is ready."
                if ready
                else "Local transcription needs a whisper.cpp executable path and a local model path before recording can be transcribed."
            ),
            details={
                "reason": "ok" if ready else "not_configured",
                "executable_path": settings.stt_executable_path,
                "model_path": settings.stt_model_path,
            },
        )

    if kind == "task_extraction":
        provider_name = settings.task_extraction_provider
        model_name = settings.extraction_model
    else:
        provider_name = settings.recap_narrative_provider
        model_name = settings.recap_model

    if provider_name == "off":
        return ProviderCheckResponse(
            kind=kind,
            provider_name=provider_name,
            ok=True,
            model_name=model_name,
            message="This provider is intentionally off.",
        )

    if provider_name == "mock":
        return ProviderCheckResponse(
            kind=kind,
            provider_name=provider_name,
            ok=True,
            model_name=model_name,
            message="Mock mode is available for local testing.",
        )

    if provider_name != "ollama":
        return ProviderCheckResponse(
            kind=kind,
            provider_name=provider_name,
            ok=False,
            model_name=model_name,
            message=f"No diagnostics are available for provider '{provider_name}' yet.",
        )

    normalized_base_url = normalize_ollama_base_url(settings.ollama_base_url)
    tags_url = build_ollama_tags_url(normalized_base_url)
    try:
        response = httpx.get(tags_url, timeout=min(settings.extraction_timeout_seconds, 8))
        response.raise_for_status()
    except httpx.TimeoutException:
        return ProviderCheckResponse(
            kind=kind,
            provider_name="ollama",
            ok=False,
            model_name=model_name,
            normalized_base_url=normalized_base_url,
            message=f"Ollama did not respond in time at {normalized_base_url}.",
            details={"reason": "provider_timeout"},
        )
    except httpx.ConnectError:
        return ProviderCheckResponse(
            kind=kind,
            provider_name="ollama",
            ok=False,
            model_name=model_name,
            normalized_base_url=normalized_base_url,
            message=f"Could not reach Ollama at {normalized_base_url}. {ollama_base_url_help_text(normalized_base_url)}",
            details={"reason": "provider_unavailable"},
        )
    except httpx.HTTPStatusError as exc:
        message = (
            f"Ollama returned HTTP {exc.response.status_code} while checking {normalized_base_url}. "
            f"{ollama_base_url_help_text(normalized_base_url)}"
            if exc.response.status_code == 404
            else f"Ollama returned HTTP {exc.response.status_code} while checking {normalized_base_url}."
        )
        return ProviderCheckResponse(
            kind=kind,
            provider_name="ollama",
            ok=False,
            model_name=model_name,
            normalized_base_url=normalized_base_url,
            message=message,
            details={"reason": "provider_unavailable", "status_code": exc.response.status_code},
        )
    except httpx.HTTPError as exc:
        return ProviderCheckResponse(
            kind=kind,
            provider_name="ollama",
            ok=False,
            model_name=model_name,
            normalized_base_url=normalized_base_url,
            message=f"Ollama health check failed: {exc}",
            details={"reason": "provider_unavailable"},
        )

    body = response.json()
    model_names = _extract_model_names(body)
    has_model = model_name in model_names if model_name else True
    message = (
        f"Ollama is reachable at {normalized_base_url} and model '{model_name}' is available."
        if has_model and model_name
        else f"Ollama is reachable at {normalized_base_url}, but model '{model_name}' was not listed."
        if model_name
        else f"Ollama is reachable at {normalized_base_url}."
    )
    return ProviderCheckResponse(
        kind=kind,
        provider_name="ollama",
        ok=has_model or not model_name,
        model_name=model_name,
        normalized_base_url=normalized_base_url,
        message=message,
        details={"reason": "ok" if has_model or not model_name else "model_missing", "available_models": model_names[:12]},
    )
