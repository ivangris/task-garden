from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Query

from app.db.session import get_db
from app.repositories.sqlalchemy import (
    SqlAlchemyActivityEventRepository,
    SqlAlchemyProjectRepository,
    SqlAlchemyTaskRepository,
)
from app.schemas.tasks import CreateTaskRequest, TaskListResponse, TaskResponse, UpdateTaskRequest
from app.services.tasks import complete_task, create_task, reopen_task, update_task

router = APIRouter()


def _build_task_response(task: object, project_name: str | None) -> TaskResponse:
    payload = TaskResponse.model_validate(task)
    return payload.model_copy(update={"project_name": project_name})


@router.post("", response_model=TaskResponse, status_code=201)
def post_task(payload: CreateTaskRequest, db: Session = Depends(get_db)) -> TaskResponse:
    task = create_task(
        payload,
        SqlAlchemyTaskRepository(db),
        SqlAlchemyProjectRepository(db),
        SqlAlchemyActivityEventRepository(db),
    )
    db.commit()
    project = SqlAlchemyProjectRepository(db).get(task.project_id) if task.project_id else None
    return _build_task_response(task, project.name if project else None)


@router.get("", response_model=TaskListResponse)
def list_tasks(
    status: str | None = Query(default=None),
    project_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> TaskListResponse:
    task_repo = SqlAlchemyTaskRepository(db)
    project_repo = SqlAlchemyProjectRepository(db)
    tasks = task_repo.list_all()
    projects = {project.id: project.name for project in project_repo.list_all()}
    filtered = [
        task
        for task in tasks
        if (status is None or task.status == status) and (project_id is None or task.project_id == project_id)
    ]
    return TaskListResponse(
        items=[_build_task_response(task, projects.get(task.project_id or "")) for task in filtered]
    )


@router.patch("/{task_id}", response_model=TaskResponse)
def patch_task(task_id: str, payload: UpdateTaskRequest, db: Session = Depends(get_db)) -> TaskResponse:
    task = update_task(
        task_id,
        payload,
        SqlAlchemyTaskRepository(db),
        SqlAlchemyProjectRepository(db),
        SqlAlchemyActivityEventRepository(db),
    )
    db.commit()
    project = SqlAlchemyProjectRepository(db).get(task.project_id) if task.project_id else None
    return _build_task_response(task, project.name if project else None)


@router.post("/{task_id}/complete", response_model=TaskResponse)
def post_complete_task(task_id: str, db: Session = Depends(get_db)) -> TaskResponse:
    task = complete_task(task_id, SqlAlchemyTaskRepository(db), SqlAlchemyActivityEventRepository(db))
    db.commit()
    project = SqlAlchemyProjectRepository(db).get(task.project_id) if task.project_id else None
    return _build_task_response(task, project.name if project else None)


@router.post("/{task_id}/reopen", response_model=TaskResponse)
def post_reopen_task(task_id: str, db: Session = Depends(get_db)) -> TaskResponse:
    task = reopen_task(task_id, SqlAlchemyTaskRepository(db), SqlAlchemyActivityEventRepository(db))
    db.commit()
    project = SqlAlchemyProjectRepository(db).get(task.project_id) if task.project_id else None
    return _build_task_response(task, project.name if project else None)
