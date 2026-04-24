from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.providers.ollama import OLLAMA_PROMPT_VERSION, OLLAMA_SCHEMA_VERSION, OllamaExtractionProvider
from app.providers.stubs import LocalStubTaskExtractionProvider
from app.providers.interfaces import ExtractionResult, TaskExtractionProvider


@dataclass(slots=True)
class EvalTarget:
    label: str
    provider_name: str
    model_name: str
    provider: TaskExtractionProvider
    schema_version: str
    prompt_version: str


def load_samples(samples_path: Path) -> list[dict[str, Any]]:
    return json.loads(samples_path.read_text(encoding="utf-8"))


def parse_target(value: str) -> tuple[str, str | None, str | None]:
    if value == "mock":
        return ("mock", None, None)
    if value.startswith("ollama:"):
        payload = value.removeprefix("ollama:")
        if "@" in payload:
            model_name, base_url = payload.split("@", maxsplit=1)
            return ("ollama", model_name, base_url)
        return ("ollama", payload, None)
    raise ValueError(f"Unsupported target '{value}'. Use 'mock' or 'ollama:<model>[@<base_url>]'.")


def build_targets(target_values: list[str]) -> list[EvalTarget]:
    settings = get_settings()
    targets: list[EvalTarget] = []
    for raw in target_values:
        provider_name, model_name, base_url = parse_target(raw)
        if provider_name == "mock":
            targets.append(
                EvalTarget(
                    label="mock",
                    provider_name="mock",
                    model_name="task-garden-mock-v1",
                    provider=LocalStubTaskExtractionProvider(),
                    schema_version="0.1.0",
                    prompt_version="phase1b-mock-extraction",
                )
            )
            continue
        resolved_model = model_name or settings.extraction_model
        resolved_base_url = base_url or settings.ollama_base_url
        targets.append(
            EvalTarget(
                label=f"ollama:{resolved_model}",
                provider_name="ollama",
                model_name=resolved_model,
                provider=OllamaExtractionProvider(
                    base_url=resolved_base_url,
                    model_name=resolved_model,
                    timeout_seconds=settings.extraction_timeout_seconds,
                ),
                schema_version=OLLAMA_SCHEMA_VERSION,
                prompt_version=OLLAMA_PROMPT_VERSION,
            )
        )
    return targets


def evaluate_sample(result: ExtractionResult, sample: dict[str, Any]) -> dict[str, Any]:
    candidates = result.candidates
    candidate_count = len(candidates)
    title_count = len([candidate for candidate in candidates if candidate.title.strip()])
    excerpt_count = len([candidate for candidate in candidates if (candidate.source_excerpt or "").strip()])
    due_date_count = len([candidate for candidate in candidates if candidate.due_date])
    labels_count = len([candidate for candidate in candidates if candidate.labels])
    min_expected = sample.get("expected_min_candidates", 0)
    max_expected = sample.get("expected_max_candidates", 999)
    expect_temporal_signal = sample.get("expect_temporal_signal", False)

    notes: list[str] = []
    if candidate_count < min_expected:
        notes.append(f"below_min({candidate_count}<{min_expected})")
    if candidate_count > max_expected:
        notes.append(f"above_max({candidate_count}>{max_expected})")
    if not expect_temporal_signal and due_date_count > 0:
        notes.append("unexpected_due_date")
    if title_count < candidate_count:
        notes.append("missing_titles")
    if excerpt_count < candidate_count:
        notes.append("missing_excerpts")
    if candidate_count == 0 and not result.open_questions:
        notes.append("no_candidates_no_questions")

    field_completeness = {
        "titles": f"{title_count}/{candidate_count or 1}",
        "excerpts": f"{excerpt_count}/{candidate_count or 1}",
        "labels": f"{labels_count}/{candidate_count or 1}",
        "due_dates": due_date_count,
    }
    return {
        "candidate_count": candidate_count,
        "field_completeness": field_completeness,
        "notes": notes,
    }


def run_target_against_samples(target: EvalTarget, samples: list[dict[str, Any]]) -> dict[str, Any]:
    sample_rows: list[dict[str, Any]] = []
    parse_successes = 0
    total_latency_ms = 0.0

    for sample in samples:
        started = time.perf_counter()
        try:
            result = target.provider.extract_tasks(
                sample["raw_text"],
                schema_version=target.schema_version,
                prompt_version=target.prompt_version,
            )
            elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
            total_latency_ms += elapsed_ms
            parse_successes += 1
            sample_eval = evaluate_sample(result, sample)
            sample_rows.append(
                {
                    "id": sample["id"],
                    "status": "ok",
                    "latency_ms": elapsed_ms,
                    "candidate_count": sample_eval["candidate_count"],
                    "titles": sample_eval["field_completeness"]["titles"],
                    "excerpts": sample_eval["field_completeness"]["excerpts"],
                    "notes": ", ".join(sample_eval["notes"]) if sample_eval["notes"] else "-",
                }
            )
        except Exception as exc:  # noqa: BLE001
            elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
            total_latency_ms += elapsed_ms
            sample_rows.append(
                {
                    "id": sample["id"],
                    "status": "error",
                    "latency_ms": elapsed_ms,
                    "candidate_count": "-",
                    "titles": "-",
                    "excerpts": "-",
                    "notes": str(exc),
                }
            )

    average_latency = round(total_latency_ms / len(samples), 2) if samples else 0.0
    return {
        "target": target.label,
        "provider": target.provider_name,
        "model": target.model_name,
        "parse_success": parse_successes,
        "sample_count": len(samples),
        "average_latency_ms": average_latency,
        "rows": sample_rows,
    }


def render_summary(result: dict[str, Any]) -> str:
    lines = [
        f"Target: {result['target']}",
        f"Parse success: {result['parse_success']}/{result['sample_count']}",
        f"Avg latency: {result['average_latency_ms']} ms",
        "Sample               Status  Count  Titles  Excerpts  Latency   Notes",
        "-------------------  ------  -----  ------  --------  --------  ------------------------------",
    ]
    for row in result["rows"]:
        lines.append(
            f"{row['id']:<19}  "
            f"{row['status']:<6}  "
            f"{str(row['candidate_count']):<5}  "
            f"{row['titles']:<6}  "
            f"{row['excerpts']:<8}  "
            f"{str(row['latency_ms']) + ' ms':<8}  "
            f"{row['notes']}"
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate local extraction providers/models against the sample corpus.")
    parser.add_argument(
        "--target",
        action="append",
        dest="targets",
        help="Evaluation target. Use 'mock' or 'ollama:<model>[@<base_url>]'. Repeat to compare multiple targets.",
    )
    parser.add_argument(
        "--samples",
        default=str(Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "extraction_samples.json"),
        help="Path to the extraction sample corpus JSON.",
    )
    parser.add_argument("--json", action="store_true", dest="as_json", help="Emit JSON instead of a readable table.")
    args = parser.parse_args()

    targets = build_targets(args.targets or ["mock"])
    samples = load_samples(Path(args.samples))
    results = [run_target_against_samples(target, samples) for target in targets]
    if args.as_json:
        print(json.dumps(results, indent=2))
        return
    print("\n\n".join(render_summary(result) for result in results))


if __name__ == "__main__":
    main()
