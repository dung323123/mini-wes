from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TelemetryIngest(BaseModel):
    robot_id: UUID
    x: float
    y: float
    theta: float = 0.0
    battery_pct: int = Field(ge=0, le=100)
    recorded_at: datetime | None = None


class TelemetryOut(BaseModel):
    id: UUID
    robot_id: UUID
    x: float
    y: float
    theta: float
    battery_pct: int
    recorded_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class TelemetryLatestItem(BaseModel):
    robot_id: UUID
    x: float
    y: float
    theta: float
    battery_pct: int
    recorded_at: datetime
