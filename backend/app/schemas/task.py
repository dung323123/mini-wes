from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.mission_step import MissionStepOut


class TaskOut(BaseModel):
    id: UUID
    code: str
    mission_type: str
    status: str
    priority: int
    order_id: UUID | None
    assigned_robot_id: UUID | None
    progress_pct: int
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskDetailOut(TaskOut):
    steps: list[MissionStepOut] = []
