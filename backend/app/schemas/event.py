from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class EventOut(BaseModel):
    id: UUID
    event_type: str
    message: str | None
    robot_id: UUID | None
    order_id: UUID | None
    mission_id: UUID | None
    created_at: datetime

    class Config:
        from_attributes = True
