from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _resolve_base_dir() -> Path:
    path = Path(__file__).resolve()
    parents = path.parents
    if len(parents) > 3:
        return parents[3]
    return parents[1]


BASE_DIR = _resolve_base_dir()
DEFAULT_SQLITE_URL = f"sqlite:///{(BASE_DIR / 'data' / 'sqlite' / 'task-garden.db').as_posix()}"
DEFAULT_AUDIO_DIR = str((BASE_DIR / "data" / "audio").resolve())
DEFAULT_BACKUP_DIR = str((BASE_DIR / "data" / "backups").resolve())
DEFAULT_CORS_ORIGINS = "http://127.0.0.1:5173,http://127.0.0.1:15173,http://localhost:5173,http://localhost:15173"


class ProviderSettings(BaseModel):
    name: str
    model: str | None = None
    base_url: str | None = None
    enabled: bool = True
    cloud: bool = False


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TASK_GARDEN_", case_sensitive=False)

    env: str = "development"
    app_name: str = "Task Garden API"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    database_url: str = Field(default=DEFAULT_SQLITE_URL)
    cors_allowed_origins: str = DEFAULT_CORS_ORIGINS
    hosted_mode: bool = False
    single_user_auth_token: str | None = None
    logging_level: str = "INFO"
    local_only_mode: bool = True
    cloud_enabled: bool = False
    auto_configure_local_defaults: bool = True

    stt_provider: str = "whisper_cpp"
    task_extraction_provider: str = "ollama"
    recap_narrative_provider: str = "ollama"
    sync_provider: str = "local_only"
    auth_provider: str = "none"

    stt_model: str = ""
    extraction_model: str = ""
    recap_model: str = ""
    ollama_base_url: str = "http://127.0.0.1:11434"
    extraction_timeout_seconds: int = 60
    sync_base_url: str | None = None
    cloud_api_key: str | None = None
    audio_storage_dir: str = DEFAULT_AUDIO_DIR
    backup_directory: str = DEFAULT_BACKUP_DIR
    stt_executable_path: str | None = None
    stt_model_path: str | None = None

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

    @property
    def write_auth_required(self) -> bool:
        return self.hosted_mode or self.auth_provider in {"bearer_token", "single_user_token"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
