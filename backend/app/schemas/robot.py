from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class RobotMissionSummary(BaseModel):
    id: UUID
    code: str
    mission_type: str
    status: str
    priority: int
    progress_pct: int

    class Config:
        from_attributes = True


class RobotOut(BaseModel):
    id: UUID
    name: str
    robot_type: str
    status: str
    battery_pct: int
    last_pose_x: float
    last_pose_y: float
    last_pose_theta: float
    last_seen_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RobotDetailOut(RobotOut):
    active_mission: RobotMissionSummary | None = None
