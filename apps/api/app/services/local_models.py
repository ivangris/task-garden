from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess

import httpx

from app.config import Settings
from app.providers.ollama_common import build_ollama_tags_url, normalize_ollama_base_url


PREFERRED_CHAT_MODELS = ("gemma3:4b", "llama3.1:8b", "qwen2.5:7b")
EMBEDDING_MODEL_MARKERS = ("embed", "embedding", "nomic-embed", "mxbai-embed", "bge-", "all-minilm")
REPO_ROOT = Path(__file__).resolve().parents[4]
PROJECT_WHISPER_EXECUTABLE = REPO_ROOT / "tools" / "whisper.cpp" / "bin" / "Release" / "whisper-cli.exe"
PROJECT_WHISPER_MODEL = REPO_ROOT / "data" / "models" / "whisper" / "ggml-base.en.bin"


@dataclass(frozen=True)
class LocalModel:
    name: str
    provider_name: str = "ollama"
    usable_for_chat: bool = True
    size: int | None = None
    modified_at: str | None = None


@dataclass(frozen=True)
class LocalProviderDefaults:
    task_extraction_provider: str
    extraction_model: str
    recap_narrative_provider: str
    recap_model: str
    stt_provider: str
    stt_model: str
    stt_ready: bool


def is_chat_model_name(model_name: str) -> bool:
    lowered = model_name.lower()
    return not any(marker in lowered for marker in EMBEDDING_MODEL_MARKERS)


def select_preferred_chat_model(model_names: list[str]) -> str | None:
    chat_models = [name for name in model_names if is_chat_model_name(name)]
    if not chat_models:
        return None
    for preferred in PREFERRED_CHAT_MODELS:
        if preferred in chat_models:
            return preferred
    return sorted(chat_models)[0]


def discover_ollama_models(settings: Settings, timeout_seconds: float = 1.5) -> list[LocalModel]:
    try:
        response = httpx.get(build_ollama_tags_url(settings.ollama_base_url), timeout=timeout_seconds)
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError):
        return discover_ollama_models_from_cli()

    models = payload.get("models") if isinstance(payload, dict) else None
    if not isinstance(models, list):
        return []

    discovered: list[LocalModel] = []
    for item in models:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if not isinstance(name, str) or not name.strip():
            continue
        discovered.append(
            LocalModel(
                name=name.strip(),
                usable_for_chat=is_chat_model_name(name),
                size=item.get("size") if isinstance(item.get("size"), int) else None,
                modified_at=item.get("modified_at") if isinstance(item.get("modified_at"), str) else None,
            )
        )
    return discovered


def discover_ollama_models_from_cli() -> list[LocalModel]:
    executable = shutil.which("ollama")
    if not executable:
        return []
    try:
        result = subprocess.run([executable, "list"], capture_output=True, text=True, check=False, timeout=4)
    except (OSError, subprocess.TimeoutExpired):
        return []
    if result.returncode != 0:
        return []

    discovered: list[LocalModel] = []
    for line in result.stdout.splitlines()[1:]:
        columns = line.split()
        if not columns:
            continue
        name = columns[0].strip()
        if ":" not in name:
            continue
        discovered.append(LocalModel(name=name, usable_for_chat=is_chat_model_name(name)))
    return discovered


def resolve_whisper_cpp_paths(settings: Settings) -> tuple[str | None, str | None]:
    executable_path = settings.stt_executable_path
    model_path = settings.stt_model_path

    if not executable_path and PROJECT_WHISPER_EXECUTABLE.exists():
        executable_path = str(PROJECT_WHISPER_EXECUTABLE)
    if not model_path and PROJECT_WHISPER_MODEL.exists():
        model_path = str(PROJECT_WHISPER_MODEL)
    return executable_path, model_path


def whisper_cpp_is_ready(settings: Settings) -> bool:
    executable_path, model_path = resolve_whisper_cpp_paths(settings)
    return bool(
        executable_path
        and model_path
        and Path(executable_path).exists()
        and Path(model_path).exists()
    )


def build_local_provider_defaults(settings: Settings, ollama_models: list[LocalModel] | None = None) -> LocalProviderDefaults:
    models = ollama_models if ollama_models is not None else discover_ollama_models(settings)
    preferred_model = select_preferred_chat_model([model.name for model in models])
    _stt_executable_path, stt_model_path = resolve_whisper_cpp_paths(settings)
    stt_ready = whisper_cpp_is_ready(settings)

    return LocalProviderDefaults(
        task_extraction_provider="ollama" if preferred_model else "mock",
        extraction_model=preferred_model or settings.extraction_model,
        recap_narrative_provider="ollama" if preferred_model else "off",
        recap_model=preferred_model or settings.recap_model,
        stt_provider="whisper_cpp" if stt_ready else "whisper_cpp",
        stt_model=Path(stt_model_path).name if stt_ready and stt_model_path else "",
        stt_ready=stt_ready,
    )


def normalized_ollama_base_url(settings: Settings) -> str:
    return normalize_ollama_base_url(settings.ollama_base_url)
