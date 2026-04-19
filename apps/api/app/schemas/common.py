from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


SourceType = Literal["typed", "pasted", "audio_transcript"]
EntryStatus = Literal["new", "transcribed", "extracted", "reviewed", "archived"]
TaskStatus = Literal["inbox", "planned", "in_progress", "blocked", "completed", "archived"]
TaskPriority = Literal["low", "medium", "high", "critical"]
TaskEffort = Literal["small", "medium", "large"]
TaskEnergy = Literal["low", "medium", "high"]


class TimestampedResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    created_at: datetime
    updated_at: datetime | None = None

