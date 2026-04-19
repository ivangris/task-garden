from fastapi import HTTPException, status

from app.domain.entities import Task
from app.repositories.interfaces import ActivityEventRepository, ProjectRepository, TaskRepository
from app.schemas.tasks import CreateTaskRequest, UpdateTaskRequest
from app.services.activity import log_activity
from app.services.common import generate_id, utcnow


def create_task(
    payload: CreateTaskRequest,
    tasks: TaskRepository,
    projects: ProjectRepository,
    activity_events: ActivityEventRepository,
) -> Task:
    if payload.project_id and projects.get(payload.project_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project not found.")

    now = utcnow()
    completed_at = now if payload.status == "completed" else None
    task = Task(
        id=generate_id(),
        title=payload.title.strip(),
        details=payload.details.strip() if payload.details else None,
        project_id=payload.project_id,
        status=payload.status,
        priority=payload.priority,
        effort=payload.effort,
        energy=payload.energy,
        source_raw_entry_id=payload.source_raw_entry_id,
        created_at=now,
        updated_at=now,
        due_date=payload.due_date,
        completed_at=completed_at,
        device_id=payload.device_id,
    )
    created = tasks.add(task)
    log_activity(
        activity_events,
        event_type="task_created",
        entity_type="task",
        entity_id=created.id,
        metadata={"status": created.status, "project_id": created.project_id},
        device_id=created.device_id,
    )
    return created


def get_task(task_id: str, tasks: TaskRepository) -> Task:
    task = tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
    return task


def update_task(
    task_id: str,
    payload: UpdateTaskRequest,
    tasks: TaskRepository,
    projects: ProjectRepository,
    activity_events: ActivityEventRepository,
) -> Task:
    task = get_task(task_id, tasks)
    changes = payload.model_dump(exclude_unset=True)

    if "project_id" in changes and payload.project_id and projects.get(payload.project_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project not found.")

    status_changed = "status" in changes and payload.status is not None and payload.status != task.status
    if "title" in changes and payload.title is not None:
        task.title = payload.title.strip()
    if "details" in changes:
        task.details = payload.details.strip() or None
    if "project_id" in changes:
        task.project_id = payload.project_id
    if "status" in changes and payload.status is not None:
        task.status = payload.status
    if "priority" in changes and payload.priority is not None:
        task.priority = payload.priority
    if "effort" in changes and payload.effort is not None:
        task.effort = payload.effort
    if "energy" in changes and payload.energy is not None:
        task.energy = payload.energy
    if "due_date" in changes:
        task.due_date = payload.due_date
    task.updated_at = utcnow()

    if status_changed and task.status == "completed":
        task.completed_at = task.updated_at
    elif status_changed and task.status != "completed":
        task.completed_at = None

    updated = tasks.update(task)
    log_activity(
        activity_events,
        event_type="task_updated",
        entity_type="task",
        entity_id=updated.id,
        metadata={"status": updated.status, "project_id": updated.project_id},
        device_id=updated.device_id,
    )
    return updated


def complete_task(task_id: str, tasks: TaskRepository, activity_events: ActivityEventRepository) -> Task:
    task = get_task(task_id, tasks)
    now = utcnow()
    task.status = "completed"
    task.completed_at = now
    task.updated_at = now
    updated = tasks.update(task)
    log_activity(
        activity_events,
        event_type="task_completed",
        entity_type="task",
        entity_id=updated.id,
        metadata={"completed_at": updated.completed_at.isoformat() if updated.completed_at else None},
        device_id=updated.device_id,
    )
    return updated


def reopen_task(task_id: str, tasks: TaskRepository, activity_events: ActivityEventRepository) -> Task:
    task = get_task(task_id, tasks)
    now = utcnow()
    task.status = "inbox"
    task.completed_at = None
    task.updated_at = now
    updated = tasks.update(task)
    log_activity(
        activity_events,
        event_type="task_reopened",
        entity_type="task",
        entity_id=updated.id,
        metadata={"status": updated.status},
        device_id=updated.device_id,
    )
    return updated
