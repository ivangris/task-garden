from app.domain.entities import Project
from app.repositories.interfaces import ActivityEventRepository, ProjectRepository
from app.schemas.projects import CreateProjectRequest
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

