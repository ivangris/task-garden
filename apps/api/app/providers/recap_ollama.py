from __future__ import annotations

import json
import time

import httpx

from app.providers.ollama_common import build_ollama_chat_url, normalize_ollama_base_url, ollama_base_url_help_text
from app.providers.extraction_common import ProviderTimeoutError, ProviderUnavailableError
from app.providers.interfaces import RecapNarrativeProvider, RecapNarrativeResult


OLLAMA_RECAP_PROMPT_VERSION = "phase7b-ollama-recap-narrative"


def build_recap_narrative_prompt(summary: dict) -> str:
    summary_json = json.dumps(summary, ensure_ascii=True)
    return (
        "Write a short reflective recap narrative from structured productivity summary data.\n"
        "Use only the facts provided.\n"
        "Do not invent metrics, project names, streaks, or emotional claims not supported by the summary.\n"
        "Keep the tone grounded, concise, and reflective.\n"
        "Weekly recaps should be practical and short.\n"
        "Monthly recaps can be slightly more reflective.\n"
        "Yearly recaps can use a stronger 'look at all you accomplished' framing, but must stay factual.\n"
        "Return plain text only, with no heading or bullet list.\n"
        "Keep it under 120 words for weekly, 150 words for monthly, and 180 words for yearly.\n\n"
        f"Summary JSON:\n{summary_json}"
    )


class OllamaRecapNarrativeProvider(RecapNarrativeProvider):
    name = "ollama"

    def __init__(self, *, base_url: str, model_name: str, timeout_seconds: int = 60) -> None:
        self.base_url = normalize_ollama_base_url(base_url)
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds

    def generate_narrative(
        self,
        summary: dict,
        prompt_version: str,
    ) -> RecapNarrativeResult:
        payload = {
            "model": self.model_name,
            "stream": False,
            "messages": [
                {"role": "system", "content": "Return only the requested narrative text."},
                {"role": "user", "content": build_recap_narrative_prompt(summary)},
            ],
            "options": {"temperature": 0.3},
        }
        url = build_ollama_chat_url(self.base_url)
        started = time.perf_counter()
        try:
            response = httpx.post(url, json=payload, timeout=self.timeout_seconds)
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError(f"Ollama recap narrative timed out after {self.timeout_seconds} seconds.") from exc
        except httpx.ConnectError as exc:
            raise ProviderUnavailableError(f"Could not reach Ollama at {self.base_url}. {ollama_base_url_help_text(self.base_url)}") from exc
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise ProviderUnavailableError(
                    f"Ollama returned HTTP 404 at {url}. {ollama_base_url_help_text(self.base_url)}"
                ) from exc
            raise ProviderUnavailableError(f"Ollama returned HTTP {exc.response.status_code} at {url}.") from exc
        except httpx.HTTPError as exc:
            raise ProviderUnavailableError(f"Ollama request failed: {exc}") from exc

        try:
            body = response.json()
        except ValueError as exc:
            raise ProviderUnavailableError("Ollama returned invalid JSON.") from exc

        message = body.get("message") if isinstance(body, dict) else None
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str) or not content.strip():
            raise ProviderUnavailableError("Ollama returned an empty recap narrative response.")

        return RecapNarrativeResult(
            narrative_text=content.strip(),
            provider_name=self.name,
            model_name=body.get("model", self.model_name),
            prompt_version=prompt_version,
            metadata={
                "base_url": self.base_url,
                "latency_ms": round((time.perf_counter() - started) * 1000, 2),
                "done": body.get("done"),
                "done_reason": body.get("done_reason"),
                "eval_count": body.get("eval_count"),
                "total_duration": body.get("total_duration"),
            },
        )
