import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Integer, DateTime, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Robot(Base):
    __tablename__ = "robots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)

    robot_type: Mapped[str] = mapped_column(String(32), nullable=False)   # AMR | MANIPULATOR | HUMANOID
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="IDLE")

    battery_pct: Mapped[int] = mapped_column(Integer, nullable=False, default=100)

    last_pose_x: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    last_pose_y: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    last_pose_theta: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))