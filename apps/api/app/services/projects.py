from fastapi import HTTPException, status

from app.domain.entities import Project
from app.repositories.interfaces import ActivityEventRepository, ProjectRepository, TaskRepository
from app.schemas.projects import CreateProjectRequest, UpdateProjectRequest
from app.services.activity import log_activity
from app.services.common import generate_id, utcnow


def create_project(
    payload: CreateProjectRequest,
    projects: ProjectRepository,
    activity_events: ActivityEventRepository,
) -> Project:
    now = utcnow()
    project = Project(
        id=generate_id(),
        name=payload.name.strip(),
        description=payload.description.strip() if payload.description else None,
        color_token=payload.color_token,
        created_at=now,
        updated_at=now,
        is_archived=False,
    )
    created = projects.add(project)
    log_activity(
        activity_events,
        event_type="project_created",
        entity_type="project",
        entity_id=created.id,
        metadata={"name": created.name},
    )
    return created


def get_project(project_id: str, projects: ProjectRepository) -> Project:
    project = projects.get(project_id)
    if project is None or project.is_archived:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    return project


def update_project(
    project_id: str,
    payload: UpdateProjectRequest,
    projects: ProjectRepository,
    activity_events: ActivityEventRepository,
) -> Project:
    project = get_project(project_id, projects)
    changes = payload.model_dump(exclude_unset=True)

    if "name" in changes and payload.name is not None:
        project.name = payload.name.strip()
    if "description" in changes:
        project.description = payload.description.strip() if payload.description else None
    if "color_token" in changes:
        project.color_token = payload.color_token
    project.updated_at = utcnow()

    updated = projects.update(project)
    log_activity(
        activity_events,
        event_type="project_updated",
        entity_type="project",
        entity_id=updated.id,
        metadata={"name": updated.name},
    )
    return updated


def delete_project(
    project_id: str,
    *,
    task_mode: str,
    projects: ProjectRepository,
    tasks: TaskRepository,
    activity_events: ActivityEventRepository,
) -> tuple[Project, int]:
    if task_mode not in {"unassign", "delete"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported project deletion mode.")

    project = get_project(project_id, projects)
    affected_tasks = tasks.list_by_project(project.id)
    now = utcnow()

    for task in affected_tasks:
        task.project_id = None
        task.updated_at = now
        if task_mode == "delete":
            task.is_deleted = True
            task.status = "archived"
            task.completed_at = None
        tasks.update(task)

    project.is_archived = True
    project.updated_at = now
    deleted = projects.update(project)
    log_activity(
        activity_events,
        event_type="project_deleted",
        entity_type="project",
        entity_id=deleted.id,
        metadata={"task_mode": task_mode, "affected_task_count": len(affected_tasks)},
    )
    return deleted, len(affected_tasks)
