import json
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ActivityEventModel, AppSettingModel, ProjectModel, RawEntryModel, TaskModel
from app.domain.entities import ActivityEvent, Project, RawEntry, Task
from app.services.common import utcnow


def _raw_entry_from_model(model: RawEntryModel) -> RawEntry:
    return RawEntry(
        id=model.id,
        source_type=model.source_type,
        raw_text=model.raw_text,
        entry_status=model.entry_status,
        created_at=model.created_at,
        updated_at=model.updated_at,
        device_id=model.device_id,
        audio_file_ref=model.audio_file_ref,
    )


def _task_from_model(model: TaskModel) -> Task:
    return Task(
        id=model.id,
        title=model.title,
        details=model.details,
        project_id=model.project_id,
        status=model.status,
        priority=model.priority,
        effort=model.effort,
        energy=model.energy,
        source_raw_entry_id=model.source_raw_entry_id,
        source_extraction_batch_id=model.source_extraction_batch_id,
        created_at=model.created_at,
        updated_at=model.updated_at,
        due_date=model.due_date,
        completed_at=model.completed_at,
        parent_task_id=model.parent_task_id,
        device_id=model.device_id,
        sync_status=model.sync_status,
        is_deleted=model.is_deleted,
    )


def _project_from_model(model: ProjectModel) -> Project:
    return Project(
        id=model.id,
        name=model.name,
        description=model.description,
        color_token=model.color_token,
        created_at=model.created_at,
        updated_at=model.updated_at,
        is_archived=model.is_archived,
    )


def _activity_from_model(model: ActivityEventModel) -> ActivityEvent:
    metadata = json.loads(model.metadata_json) if model.metadata_json else {}
    return ActivityEvent(
        id=model.id,
        event_type=model.event_type,
        entity_type=model.entity_type,
        entity_id=model.entity_id,
        metadata=metadata,
        created_at=model.created_at,
        device_id=model.device_id,
    )


class SqlAlchemyRawEntryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, entry: RawEntry) -> RawEntry:
        model = RawEntryModel(
            id=entry.id,
            source_type=entry.source_type,
            raw_text=entry.raw_text,
            audio_file_ref=entry.audio_file_ref,
            entry_status=entry.entry_status,
            device_id=entry.device_id,
            created_at=entry.created_at,
            updated_at=entry.updated_at,
        )
        self.session.add(model)
        self.session.flush()
        return _raw_entry_from_model(model)

    def get(self, entry_id: str) -> RawEntry | None:
        model = self.session.get(RawEntryModel, entry_id)
        return _raw_entry_from_model(model) if model else None

    def list_all(self) -> list[RawEntry]:
        models = self.session.scalars(select(RawEntryModel).order_by(RawEntryModel.created_at.desc())).all()
        return [_raw_entry_from_model(model) for model in models]


class SqlAlchemyTaskRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, task: Task) -> Task:
        model = TaskModel(
            id=task.id,
            title=task.title,
            details=task.details,
            project_id=task.project_id,
            status=task.status,
            priority=task.priority,
            effort=task.effort,
            energy=task.energy,
            source_raw_entry_id=task.source_raw_entry_id,
            source_extraction_batch_id=task.source_extraction_batch_id,
            created_at=task.created_at,
            updated_at=task.updated_at,
            due_date=task.due_date,
            completed_at=task.completed_at,
            parent_task_id=task.parent_task_id,
            device_id=task.device_id,
            sync_status=task.sync_status,
            is_deleted=task.is_deleted,
        )
        self.session.add(model)
        self.session.flush()
        return _task_from_model(model)

    def get(self, task_id: str) -> Task | None:
        model = self.session.get(TaskModel, task_id)
        return _task_from_model(model) if model else None

    def list_active(self) -> list[Task]:
        models = self.session.scalars(
            select(TaskModel).where(TaskModel.is_deleted.is_(False), TaskModel.status != "completed").order_by(TaskModel.created_at.desc())
        ).all()
        return [_task_from_model(model) for model in models]

    def list_all(self) -> list[Task]:
        models = self.session.scalars(
            select(TaskModel).where(TaskModel.is_deleted.is_(False)).order_by(TaskModel.created_at.desc())
        ).all()
        return [_task_from_model(model) for model in models]

    def update(self, task: Task) -> Task:
        model = self.session.get(TaskModel, task.id)
        if model is None:
            raise ValueError(f"Task {task.id} not found")

        model.title = task.title
        model.details = task.details
        model.project_id = task.project_id
        model.status = task.status
        model.priority = task.priority
        model.effort = task.effort
        model.energy = task.energy
        model.source_raw_entry_id = task.source_raw_entry_id
        model.source_extraction_batch_id = task.source_extraction_batch_id
        model.created_at = task.created_at
        model.updated_at = task.updated_at
        model.due_date = task.due_date
        model.completed_at = task.completed_at
        model.parent_task_id = task.parent_task_id
        model.device_id = task.device_id
        model.sync_status = task.sync_status
        model.is_deleted = task.is_deleted
        self.session.flush()
        return _task_from_model(model)


class SqlAlchemyProjectRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, project: Project) -> Project:
        model = ProjectModel(
            id=project.id,
            name=project.name,
            description=project.description,
            color_token=project.color_token,
            created_at=project.created_at,
            updated_at=project.updated_at,
            is_archived=project.is_archived,
        )
        self.session.add(model)
        self.session.flush()
        return _project_from_model(model)

    def list_all(self) -> list[Project]:
        models = self.session.scalars(select(ProjectModel).order_by(ProjectModel.name.asc())).all()
        return [_project_from_model(model) for model in models]

    def get(self, project_id: str) -> Project | None:
        model = self.session.get(ProjectModel, project_id)
        return _project_from_model(model) if model else None


class SqlAlchemyActivityEventRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, event: ActivityEvent) -> ActivityEvent:
        model = ActivityEventModel(
            id=event.id,
            event_type=event.event_type,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            metadata_json=json.dumps(event.metadata),
            created_at=event.created_at,
            device_id=event.device_id,
        )
        self.session.add(model)
        self.session.flush()
        return _activity_from_model(model)

    def list_recent(self, limit: int = 50) -> list[ActivityEvent]:
        models = self.session.scalars(
            select(ActivityEventModel).order_by(ActivityEventModel.created_at.desc()).limit(limit)
        ).all()
        return [_activity_from_model(model) for model in models]


class SqlAlchemySettingsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_local_settings(self) -> dict[str, str | bool | None]:
        models = self.session.scalars(select(AppSettingModel)).all()
        result: dict[str, str | bool | None] = {}
        for model in models:
            result[model.key] = json.loads(model.value) if model.value is not None else None
        return result

    def save_local_settings(self, values: dict[str, str | bool | None]) -> dict[str, str | bool | None]:
        existing = {
            model.key: model
            for model in self.session.scalars(
                select(AppSettingModel).where(AppSettingModel.key.in_(list(values.keys())))
            ).all()
        }

        for key, value in values.items():
            model = existing.get(key)
            if model is None:
                model = AppSettingModel(key=key, updated_at=utcnow())
                self.session.add(model)
            model.value = json.dumps(value) if value is not None else None
            model.updated_at = utcnow()
        self.session.flush()
        return self.get_local_settings()
