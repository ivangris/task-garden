from dataclasses import asdict

from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends

from app.db.session import get_db
from app.repositories.sqlalchemy import (
    SqlAlchemyActivityEventRepository,
    SqlAlchemyExtractedTaskCandidateRepository,
    SqlAlchemyExtractionBatchRepository,
    SqlAlchemyProjectRepository,
    SqlAlchemyRawEntryRepository,
    SqlAlchemyTaskRepository,
)
from app.schemas.extractions import ConfirmExtractionRequest, ConfirmExtractionResponse, ExtractionBatchResponse, ExtractionCandidateResponse
from app.services.extractions import confirm_extraction, get_extraction

router = APIRouter()


@router.get("/{extraction_id}", response_model=ExtractionBatchResponse)
def fetch_extraction(extraction_id: str, db: Session = Depends(get_db)) -> ExtractionBatchResponse:
    batch, candidates = get_extraction(
        extraction_id,
        SqlAlchemyExtractionBatchRepository(db),
        SqlAlchemyExtractedTaskCandidateRepository(db),
    )
    return ExtractionBatchResponse(
        **asdict(batch),
        candidates=[ExtractionCandidateResponse.model_validate(candidate) for candidate in candidates],
    )


@router.post("/{extraction_id}/confirm", response_model=ConfirmExtractionResponse)
def post_confirm_extraction(
    extraction_id: str,
    payload: ConfirmExtractionRequest,
    db: Session = Depends(get_db),
) -> ConfirmExtractionResponse:
    created_task_ids, updated_candidates = confirm_extraction(
        extraction_id,
        payload,
        SqlAlchemyExtractionBatchRepository(db),
        SqlAlchemyExtractedTaskCandidateRepository(db),
        SqlAlchemyRawEntryRepository(db),
        SqlAlchemyTaskRepository(db),
        SqlAlchemyProjectRepository(db),
        SqlAlchemyActivityEventRepository(db),
    )
    db.commit()
    rejected_count = len([candidate for candidate in updated_candidates if candidate.candidate_status == "rejected"])
    accepted_count = len(updated_candidates) - rejected_count
    return ConfirmExtractionResponse(
        extraction_id=extraction_id,
        created_task_ids=created_task_ids,
        accepted_count=accepted_count,
        rejected_count=rejected_count,
        updated_candidates=[ExtractionCandidateResponse.model_validate(candidate) for candidate in updated_candidates],
    )
