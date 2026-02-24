from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class Pose(BaseModel):
    x: float
    y: float
    theta: float


class RobotOut(BaseModel):
    id: UUID
    name: str
    robot_type: str
    status: str
    battery_pct: int
    last_pose: Pose
    last_seen_at: datetime

    class Config:
        from_attributes = True