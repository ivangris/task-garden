from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[3]
DEFAULT_SQLITE_URL = f"sqlite:///{(BASE_DIR / 'data' / 'sqlite' / 'task-garden.db').as_posix()}"


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
    local_only_mode: bool = True
    cloud_enabled: bool = False

    stt_provider: str = "local_stub"
    task_extraction_provider: str = "local_stub"
    sync_provider: str = "local_only"
    auth_provider: str = "none"

    stt_model: str = "whisper-local-placeholder"
    extraction_model: str = "ollama-local-placeholder"
    sync_base_url: str | None = None
    cloud_api_key: str | None = None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
