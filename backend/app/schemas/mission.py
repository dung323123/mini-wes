from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.mission_step import MissionStepCreate, MissionStepOut


class MissionCreate(BaseModel):
    mission_type: str
    priority: int = 5
    steps: list[MissionStepCreate]


class MissionAssign(BaseModel):
    robot_id: UUID


class MissionOut(BaseModel):
    id: UUID
    code: str
    mission_type: str
    status: str
    priority: int
    assigned_robot_id: UUID | None
    progress_pct: int
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    updated_at: datetime

    steps: list[MissionStepOut] = []

    class Config:
        from_attributes = True