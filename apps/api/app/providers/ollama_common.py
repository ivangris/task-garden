from __future__ import annotations

from urllib.parse import urlsplit, urlunsplit


def normalize_ollama_base_url(base_url: str) -> str:
    trimmed = (base_url or "").strip().rstrip("/")
    if not trimmed:
        return "http://127.0.0.1:11434"

    parts = urlsplit(trimmed)
    path = parts.path.rstrip("/")
    for suffix in ("/api/chat", "/api/generate", "/api/tags", "/api"):
        if path.endswith(suffix):
            path = path[: -len(suffix)]
            break
    normalized_path = path.rstrip("/")
    normalized = urlunsplit((parts.scheme or "http", parts.netloc, normalized_path, "", ""))
    return normalized.rstrip("/")


def build_ollama_chat_url(base_url: str) -> str:
    return f"{normalize_ollama_base_url(base_url)}/api/chat"


def build_ollama_tags_url(base_url: str) -> str:
    return f"{normalize_ollama_base_url(base_url)}/api/tags"


def ollama_base_url_help_text(base_url: str) -> str:
    normalized = normalize_ollama_base_url(base_url)
    return (
        f"Use the Ollama server root URL, for example {normalized}. "
        "Do not include /api or /api/chat in the saved base URL."
    )
