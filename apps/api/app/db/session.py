from functools import lru_cache
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings


def resolve_database_url(database_url: str) -> str:
    if not database_url.startswith("sqlite:///"):
        return database_url

    relative_path = database_url.removeprefix("sqlite:///")
    if Path(relative_path).is_absolute():
        resolved = Path(relative_path)
    else:
        base_dir = Path(__file__).resolve().parents[4]
        resolved = (base_dir / relative_path).resolve()

    resolved.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{resolved.as_posix()}"


def sqlite_database_path(database_url: str) -> Path | None:
    resolved_url = resolve_database_url(database_url)
    if not resolved_url.startswith("sqlite:///"):
        return None

    database_path = resolved_url.removeprefix("sqlite:///")
    if database_path == ":memory:":
        return None
    return Path(database_path).resolve()


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    return create_engine(resolve_database_url(get_settings().database_url), future=True)


@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
