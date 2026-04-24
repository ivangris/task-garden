from dataclasses import asdict

from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException

from app.config import get_settings
from app.db.session import get_db
from app.providers.ollama import OLLAMA_PROMPT_VERSION, OLLAMA_SCHEMA_VERSION
from app.repositories.sqlalchemy import (
    SqlAlchemyActivityEventRepository,
    SqlAlchemyExtractedTaskCandidateRepository,
    SqlAlchemyExtractionBatchRepository,
    SqlAlchemyRawEntryRepository,
    SqlAlchemySettingsRepository,
)
from app.schemas.extractions import ExtractionBatchResponse, ExtractionCandidateResponse
from app.services.extractions import run_extraction_for_entry
from app.services.provider_registry import build_task_extraction_provider
from app.services.settings import get_settings_payload

router = APIRouter()


@router.post("/{entry_id}/extract", response_model=ExtractionBatchResponse, status_code=201)
def post_extract_entry(entry_id: str, db: Session = Depends(get_db)) -> ExtractionBatchResponse:
    defaults = get_settings()
    effective_settings = defaults.model_copy(
        update=get_settings_payload(SqlAlchemySettingsRepository(db), defaults).model_dump()
    )
    provider = build_task_extraction_provider(effective_settings)
    schema_version = OLLAMA_SCHEMA_VERSION if provider.name == "ollama" else "0.1.0"
    prompt_version = OLLAMA_PROMPT_VERSION if provider.name == "ollama" else "phase1b-mock-extraction"
    try:
        batch, candidates = run_extraction_for_entry(
            entry_id,
            SqlAlchemyRawEntryRepository(db),
            SqlAlchemyExtractionBatchRepository(db),
            SqlAlchemyExtractedTaskCandidateRepository(db),
            SqlAlchemyActivityEventRepository(db),
            provider,
            schema_version=schema_version,
            prompt_version=prompt_version,
        )
        db.commit()
        return ExtractionBatchResponse(
            **asdict(batch),
            candidates=[ExtractionCandidateResponse.model_validate(candidate) for candidate in candidates],
        )
    except HTTPException:
        db.commit()
        raise
