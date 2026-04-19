from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import TaskEffort, TaskEnergy, TaskPriority, TaskStatus


class CreateTaskRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    details: str | None = Field(default=None, max_length=4000)
    project_id: str | None = None
    status: TaskStatus = "inbox"
    priority: TaskPriority = "medium"
    effort: TaskEffort = "medium"
    energy: TaskEnergy = "medium"
    due_date: datetime | None = None
    source_raw_entry_id: str | None = None
    device_id: str | None = Field(default=None, max_length=64)


class UpdateTaskRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    details: str | None = Field(default=None, max_length=4000)
    project_id: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    effort: TaskEffort | None = None
    energy: TaskEnergy | None = None
    due_date: datetime | None = None


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    details: str | None = None
    project_id: str | None = None
    project_name: str | None = None
    status: TaskStatus
    priority: TaskPriority
    effort: TaskEffort
    energy: TaskEnergy
    source_raw_entry_id: str | None = None
    created_at: datetime
    updated_at: datetime
    due_date: datetime | None = None
    completed_at: datetime | None = None
    device_id: str | None = None


class TaskListResponse(BaseModel):
    items: list[TaskResponse]
