from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Header, Query

from app.db.session import get_db
from app.repositories.sqlalchemy import (
    SqlAlchemyActivityEventRepository,
    SqlAlchemyChangeEventRepository,
    SqlAlchemyProjectRepository,
    SqlAlchemyTaskRepository,
)
from app.schemas.projects import CreateProjectRequest, DeleteProjectResponse, ProjectListResponse, ProjectResponse, UpdateProjectRequest
from app.services.sync import record_change_event, snapshot_project
from app.services.projects import create_project, delete_project, update_project

router = APIRouter()


@router.get("", response_model=ProjectListResponse)
def list_projects(db: Session = Depends(get_db)) -> ProjectListResponse:
    items = SqlAlchemyProjectRepository(db).list_all()
    return ProjectListResponse(items=[ProjectResponse.model_validate(item) for item in items if not item.is_archived])


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


@router.patch("/{project_id}", response_model=ProjectResponse)
def patch_project(
    project_id: str,
    payload: UpdateProjectRequest,
    db: Session = Depends(get_db),
    device_id: str | None = Header(default=None, alias="X-Task-Garden-Device-Id"),
) -> ProjectResponse:
    project = update_project(
        project_id,
        payload,
        SqlAlchemyProjectRepository(db),
        SqlAlchemyActivityEventRepository(db),
    )
    record_change_event(
        SqlAlchemyChangeEventRepository(db),
        entity_type="project",
        entity_id=project.id,
        change_type="updated",
        payload=snapshot_project(project),
        device_id=device_id,
    )
    db.commit()
    return ProjectResponse.model_validate(project)


@router.delete("/{project_id}", response_model=DeleteProjectResponse)
def delete_project_route(
    project_id: str,
    task_mode: str = Query(default="unassign", pattern="^(unassign|delete)$"),
    db: Session = Depends(get_db),
    device_id: str | None = Header(default=None, alias="X-Task-Garden-Device-Id"),
) -> DeleteProjectResponse:
    project, affected_task_count = delete_project(
        project_id,
        task_mode=task_mode,
        projects=SqlAlchemyProjectRepository(db),
        tasks=SqlAlchemyTaskRepository(db),
        activity_events=SqlAlchemyActivityEventRepository(db),
    )
    record_change_event(
        SqlAlchemyChangeEventRepository(db),
        entity_type="project",
        entity_id=project.id,
        change_type="deleted",
        payload={**snapshot_project(project), "task_mode": task_mode, "affected_task_count": affected_task_count},
        device_id=device_id,
    )
    db.commit()
    return DeleteProjectResponse(project_id=project.id, task_mode=task_mode, affected_task_count=affected_task_count)
