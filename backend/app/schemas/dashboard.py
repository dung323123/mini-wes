from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CountItem(BaseModel):
    key: str
    count: int


class DashboardSummaryOut(BaseModel):
    robots_total: int
    robots_by_status: list[CountItem]
    orders_by_status: list[CountItem]
    tasks_by_status: list[CountItem]
    tasks_running: int


class FleetRobotItem(BaseModel):
    robot_id: UUID
    name: str
    robot_type: str
    status: str
    battery_pct: int
    x: float
    y: float
    theta: float
    last_seen_at: datetime
    active_task_id: UUID | None
    active_task_code: str | None
    active_task_status: str | None
