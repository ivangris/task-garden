from __future__ import annotations

import json
import time

import httpx

from app.providers.ollama_common import build_ollama_chat_url, normalize_ollama_base_url, ollama_base_url_help_text
from app.providers.extraction_common import (
    EmptyExtractionResponseError,
    LowSignalExtractionError,
    MalformedStructuredOutputError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from app.providers.interfaces import ExtractedTaskCandidateResult, ExtractionResult, TaskExtractionProvider
from app.schemas.extractions import ProviderExtractionEnvelope


OLLAMA_SCHEMA_VERSION = "0.2.0"
OLLAMA_PROMPT_VERSION = "phase3a-ollama-extraction"


def build_ollama_prompt(raw_text: str) -> str:
    schema_json = json.dumps(ProviderExtractionEnvelope.model_json_schema())
    return (
        "You extract likely task candidates from a raw personal productivity note.\n"
        "Return only reviewable, actionable tasks and never bypass human review.\n"
        "Split only when the note clearly contains separate actions.\n"
        "Do not split a single task into fragments unless the text clearly names distinct actions.\n"
        "Write short, concrete titles that start with a verb when natural.\n"
        "Keep details factual and restrained.\n"
        "Do not invent projects, labels, parent tasks, or due dates without textual support.\n"
        "Be conservative with due_date. Only include it when the text clearly signals timing such as today, tomorrow, this week, or a specific date.\n"
        "Use priority, effort, and energy consistently and conservatively.\n"
        "If the note is vague, uncertain, or mostly context, prefer fewer candidates and use open_questions.\n"
        "If there is not enough signal for any candidate, return zero candidates and explain the gap in open_questions.\n"
        "Return JSON matching this schema exactly:\n"
        f"{schema_json}\n\n"
        f"Raw entry:\n{raw_text}"
    )


def build_ollama_json_prompt(raw_text: str) -> str:
    return (
        "Extract likely task candidates from the raw personal productivity note below.\n"
        "Return only valid JSON. Do not include markdown, commentary, or the schema itself.\n"
        "Use this exact top-level shape:\n"
        "{\n"
        '  "summary": "short summary or null",\n'
        '  "open_questions": ["short question if review is needed"],\n'
        '  "candidates": [\n'
        "    {\n"
        '      "title": "short actionable task title",\n'
        '      "details": "factual detail or null",\n'
        '      "project_or_group": "project name if explicit, otherwise null",\n'
        '      "priority": "low|medium|high|critical",\n'
        '      "effort": "small|medium|large",\n'
        '      "energy": "low|medium|high",\n'
        '      "labels": ["only labels clearly supported by the note"],\n'
        '      "due_date": "ISO-like date string only if explicit, otherwise null",\n'
        '      "parent_task_title": null,\n'
        '      "confidence": 0.0,\n'
        '      "source_excerpt": "short quote or paraphrase from source"\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "Split only clearly separate actions. Do not invent tasks, projects, labels, or due dates.\n"
        "If there is not enough signal, return an empty candidates array and explain in open_questions.\n\n"
        f"Raw entry:\n{raw_text}"
    )


class OllamaExtractionProvider(TaskExtractionProvider):
    name = "ollama"

    def __init__(self, *, base_url: str, model_name: str, timeout_seconds: int = 60) -> None:
        self.base_url = normalize_ollama_base_url(base_url)
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds

    def extract_tasks(
        self,
        raw_text: str,
        schema_version: str,
        prompt_version: str,
        context: dict | None = None,
    ) -> ExtractionResult:
        body, started, response_format = self._post_extraction_request(raw_text)

        message = body.get("message") if isinstance(body, dict) else None
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str) or not content.strip():
            raise EmptyExtractionResponseError("Ollama returned an empty extraction response.")

        try:
            parsed = ProviderExtractionEnvelope.model_validate_json(content)
        except Exception as exc:  # noqa: BLE001
            raise MalformedStructuredOutputError() from exc

        if not parsed.candidates and not parsed.open_questions:
            raise LowSignalExtractionError("Ollama returned no candidates and no open questions.")

        candidates = [
            ExtractedTaskCandidateResult(
                title=candidate.title.strip(),
                details=candidate.details.strip() if candidate.details else None,
                project_or_group=candidate.project_or_group.strip() if candidate.project_or_group else None,
                priority=candidate.priority,
                effort=candidate.effort,
                energy=candidate.energy,
                labels=candidate.labels,
                due_date=candidate.due_date,
                parent_task_title=candidate.parent_task_title.strip() if candidate.parent_task_title else None,
                confidence=candidate.confidence,
                source_excerpt=candidate.source_excerpt.strip() if candidate.source_excerpt else None,
            )
            for candidate in parsed.candidates
        ]
        return ExtractionResult(
            provider_name=self.name,
            model_name=body.get("model", self.model_name),
            schema_version=schema_version,
            prompt_version=prompt_version,
            summary=parsed.summary,
            needs_review=True,
            open_questions=parsed.open_questions,
            candidates=candidates,
            metadata={
                "base_url": self.base_url,
                "latency_ms": round((time.perf_counter() - started) * 1000, 2),
                "done": body.get("done"),
                "done_reason": body.get("done_reason"),
                "eval_count": body.get("eval_count"),
                "total_duration": body.get("total_duration"),
                "response_format": response_format,
                "raw_response": json.dumps(body),
            },
        )

    def _post_extraction_request(self, raw_text: str) -> tuple[dict, float, str]:
        payload = {
            "model": self.model_name,
            "stream": False,
            "format": ProviderExtractionEnvelope.model_json_schema(),
            "messages": [
                {
                    "role": "system",
                    "content": "Return valid JSON matching the provided schema.",
                },
                {
                    "role": "user",
                    "content": build_ollama_prompt(raw_text),
                },
            ],
            "options": {"temperature": 0},
        }
        url = build_ollama_chat_url(self.base_url)
        started = time.perf_counter()
        response_format = "json_schema"
        try:
            response = httpx.post(url, json=payload, timeout=self.timeout_seconds)
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError(f"Ollama timed out after {self.timeout_seconds} seconds.") from exc
        except httpx.ConnectError as exc:
            raise ProviderUnavailableError(f"Could not reach Ollama at {self.base_url}. {ollama_base_url_help_text(self.base_url)}") from exc
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise ProviderUnavailableError(
                    f"Ollama returned HTTP 404 at {url}. {ollama_base_url_help_text(self.base_url)}"
                ) from exc
            if exc.response.status_code == 500 and "failed to load model vocabulary required for format" in exc.response.text:
                retry_payload = {
                    **payload,
                    "format": "json",
                    "messages": [
                        {
                            "role": "system",
                            "content": "Return valid JSON only.",
                        },
                        {
                            "role": "user",
                            "content": build_ollama_json_prompt(raw_text),
                        },
                    ],
                }
                response_format = "json"
                try:
                    response = httpx.post(url, json=retry_payload, timeout=self.timeout_seconds)
                    response.raise_for_status()
                except httpx.TimeoutException as retry_exc:
                    raise ProviderTimeoutError(f"Ollama timed out after {self.timeout_seconds} seconds.") from retry_exc
                except httpx.HTTPStatusError as retry_exc:
                    detail = retry_exc.response.text.strip()
                    raise ProviderUnavailableError(
                        f"Ollama returned HTTP {retry_exc.response.status_code} at {url}. {detail}"
                    ) from retry_exc
                except httpx.HTTPError as retry_exc:
                    raise ProviderUnavailableError(f"Ollama request failed: {retry_exc}") from retry_exc
            else:
                detail = exc.response.text.strip()
                suffix = f" {detail}" if detail else ""
                raise ProviderUnavailableError(f"Ollama returned HTTP {exc.response.status_code} at {url}.{suffix}") from exc
        except httpx.HTTPError as exc:
            raise ProviderUnavailableError(f"Ollama request failed: {exc}") from exc

        try:
            body = response.json()
        except ValueError as exc:
            raise MalformedStructuredOutputError("Ollama did not return valid JSON at the API boundary.") from exc
        return body, started, response_format
