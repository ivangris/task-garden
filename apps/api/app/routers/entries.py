from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends

from app.db.session import get_db
from app.repositories.sqlalchemy import SqlAlchemyActivityEventRepository, SqlAlchemyRawEntryRepository
from app.schemas.entries import CreateEntryRequest, RawEntryListResponse, RawEntryResponse
from app.services.entries import create_raw_entry, get_raw_entry

router = APIRouter()


@router.post("", response_model=RawEntryResponse, status_code=201)
def post_entry(payload: CreateEntryRequest, db: Session = Depends(get_db)) -> RawEntryResponse:
    entry = create_raw_entry(
        payload,
        SqlAlchemyRawEntryRepository(db),
        SqlAlchemyActivityEventRepository(db),
    )
    db.commit()
    return RawEntryResponse.model_validate(entry)


@router.get("/{entry_id}", response_model=RawEntryResponse)
def fetch_entry(entry_id: str, db: Session = Depends(get_db)) -> RawEntryResponse:
    entry = get_raw_entry(entry_id, SqlAlchemyRawEntryRepository(db))
    return RawEntryResponse.model_validate(entry)


@router.get("", response_model=RawEntryListResponse)
def list_entries(db: Session = Depends(get_db)) -> RawEntryListResponse:
    entries = SqlAlchemyRawEntryRepository(db).list_all()
    return RawEntryListResponse(items=[RawEntryResponse.model_validate(entry) for entry in entries])
