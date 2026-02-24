from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class MissionStepCreate(BaseModel):
    seq: int
    action: str


class MissionStepOut(BaseModel):
    id: UUID
    mission_id: UUID
    seq: int
    action: str
    status: str
    started_at: datetime | None
    finished_at: datetime | None

    class Config:
        from_attributes = True