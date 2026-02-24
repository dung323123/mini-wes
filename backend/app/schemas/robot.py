from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


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


class RobotCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    robot_type: str = Field(min_length=1, max_length=32)
    status: str = "IDLE"
    battery_pct: int = Field(default=100, ge=0, le=100)
    last_pose_x: float = 0.0
    last_pose_y: float = 0.0
    last_pose_theta: float = 0.0


class RobotUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    robot_type: str | None = Field(default=None, min_length=1, max_length=32)
    status: str | None = None
    battery_pct: int | None = Field(default=None, ge=0, le=100)
    last_pose_x: float | None = None
    last_pose_y: float | None = None
    last_pose_theta: float | None = None
    enabled: bool | None = None
