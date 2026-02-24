from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.event import Event
from app.schemas.event import EventOut

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=list[EventOut])
def list_events(
    type: str | None = Query(default=None, alias="type"),
    robot_id: UUID | None = Query(default=None),
    order_id: UUID | None = Query(default=None),
    mission_id: UUID | None = Query(default=None),
    from_ts: datetime | None = Query(default=None, alias="from"),
    to_ts: datetime | None = Query(default=None, alias="to"),
    limit: int = Query(default=200, ge=1, le=5000),
    db: Session = Depends(get_db),
):
    stmt = select(Event).order_by(desc(Event.created_at)).limit(limit)
    if type:
        stmt = stmt.where(Event.event_type == type)
    if robot_id:
        stmt = stmt.where(Event.robot_id == robot_id)
    if order_id:
        stmt = stmt.where(Event.order_id == order_id)
    if mission_id:
        stmt = stmt.where(Event.mission_id == mission_id)
    if from_ts:
        stmt = stmt.where(Event.created_at >= from_ts)
    if to_ts:
        stmt = stmt.where(Event.created_at <= to_ts)
    return db.execute(stmt).scalars().all()
