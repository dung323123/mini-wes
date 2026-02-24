from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AllocatorRunRequest(BaseModel):
    max_orders: int = Field(default=20, ge=1, le=200)
    battery_min_pct: int = Field(default=20, ge=0, le=100)


class AllocationAssigned(BaseModel):
    order_id: UUID
    mission_id: UUID
    robot_id: UUID
    score: float
    distance: float


class AllocationUnassigned(BaseModel):
    order_id: UUID
    reason: str


class AllocationSummary(BaseModel):
    total: int
    assigned: int
    unassigned: int


class AllocatorRunResponse(BaseModel):
    run_id: UUID
    assigned: list[AllocationAssigned]
    unassigned: list[AllocationUnassigned]
    summary: AllocationSummary


class AllocatorRunItemOut(BaseModel):
    order_id: UUID
    robot_id: UUID | None
    mission_id: UUID | None
    result: str
    reason: str | None
    score: float | None
    distance: float | None
    created_at: datetime

    class Config:
        from_attributes = True


class AllocatorRunDetailOut(BaseModel):
    id: UUID
    status: str
    battery_min_pct: int
    max_orders: int
    total_orders: int
    assigned_count: int
    unassigned_count: int
    created_at: datetime
    completed_at: datetime | None
    items: list[AllocatorRunItemOut]

    class Config:
        from_attributes = True
