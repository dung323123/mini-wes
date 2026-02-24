from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class Point(BaseModel):
    x: float
    y: float


class OrderCreate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=64)
    pickup_location: Point
    dropoff_location: Point
    priority: int = Field(default=5, ge=1, le=10)


class OrderUpdate(BaseModel):
    priority: int | None = Field(default=None, ge=1, le=10)
    status: str | None = None


class OrderOut(BaseModel):
    id: UUID
    code: str
    pickup_x: float
    pickup_y: float
    dropoff_x: float
    dropoff_y: float
    priority: int
    status: str
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
