from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends

from app.db.session import get_db
from app.repositories.sqlalchemy import SqlAlchemyActivityEventRepository, SqlAlchemyProjectRepository
from app.schemas.projects import CreateProjectRequest, ProjectListResponse, ProjectResponse
from app.services.projects import create_project

router = APIRouter()


@router.get("", response_model=ProjectListResponse)
def list_projects(db: Session = Depends(get_db)) -> ProjectListResponse:
    items = SqlAlchemyProjectRepository(db).list_all()
    return ProjectListResponse(items=[ProjectResponse.model_validate(item) for item in items])


@router.post("", response_model=ProjectResponse, status_code=201)
def post_project(payload: CreateProjectRequest, db: Session = Depends(get_db)) -> ProjectResponse:
    project = create_project(
        payload,
        SqlAlchemyProjectRepository(db),
        SqlAlchemyActivityEventRepository(db),
    )
    db.commit()
    return ProjectResponse.model_validate(project)
