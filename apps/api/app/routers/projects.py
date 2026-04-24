from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Header

from app.db.session import get_db
from app.repositories.sqlalchemy import (
    SqlAlchemyActivityEventRepository,
    SqlAlchemyChangeEventRepository,
    SqlAlchemyProjectRepository,
)
from app.schemas.projects import CreateProjectRequest, ProjectListResponse, ProjectResponse
from app.services.sync import record_change_event, snapshot_project
from app.services.projects import create_project

router = APIRouter()


@router.get("", response_model=ProjectListResponse)
def list_projects(db: Session = Depends(get_db)) -> ProjectListResponse:
    items = SqlAlchemyProjectRepository(db).list_all()
    return ProjectListResponse(items=[ProjectResponse.model_validate(item) for item in items])


@router.post("", response_model=ProjectResponse, status_code=201)
def post_project(
    payload: CreateProjectRequest,
    db: Session = Depends(get_db),
    device_id: str | None = Header(default=None, alias="X-Task-Garden-Device-Id"),
) -> ProjectResponse:
    project = create_project(
        payload,
        SqlAlchemyProjectRepository(db),
        SqlAlchemyActivityEventRepository(db),
    )
    record_change_event(
        SqlAlchemyChangeEventRepository(db),
        entity_type="project",
        entity_id=project.id,
        change_type="upserted",
        payload=snapshot_project(project),
        device_id=device_id,
    )
    db.commit()
    return ProjectResponse.model_validate(project)
