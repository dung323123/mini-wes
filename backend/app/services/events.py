from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.event import Event


def _now():
    return datetime.now(timezone.utc)


def log_event(
    db: Session,
    event_type: str,
    message: str | None = None,
    robot_id: UUID | None = None,
    order_id: UUID | None = None,
    mission_id: UUID | None = None,
) -> Event:
    evt = Event(
        event_type=event_type,
        message=message,
        robot_id=robot_id,
        order_id=order_id,
        mission_id=mission_id,
        created_at=_now(),
    )
    db.add(evt)
    return evt
