from app.domain.entities import ActivityEvent
from app.repositories.interfaces import ActivityEventRepository
from app.services.common import generate_id, utcnow


def log_activity(
    repository: ActivityEventRepository,
    *,
    event_type: str,
    entity_type: str,
    entity_id: str,
    metadata: dict[str, object] | None = None,
    device_id: str | None = None,
) -> ActivityEvent:
    event = ActivityEvent(
        id=generate_id(),
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata=metadata or {},
        created_at=utcnow(),
        device_id=device_id,
    )
    return repository.add(event)

