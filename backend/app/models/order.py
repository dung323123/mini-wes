import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Integer, DateTime, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)

    pickup_x: Mapped[float] = mapped_column(Float, nullable=False)
    pickup_y: Mapped[float] = mapped_column(Float, nullable=False)
    dropoff_x: Mapped[float] = mapped_column(Float, nullable=False)
    dropoff_y: Mapped[float] = mapped_column(Float, nullable=False)

    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="CREATED")

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
