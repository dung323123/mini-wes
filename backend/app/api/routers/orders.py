from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.order import Order
from app.schemas.order import OrderCreate, OrderOut, OrderUpdate
from app.services.events import log_event

router = APIRouter(prefix="/orders", tags=["orders"])


def _now():
    return datetime.now(timezone.utc)


def _make_order_code(db: Session) -> str:
    today = _now().strftime("%Y%m%d")
    like = f"ORD-{today}-%"
    n = db.execute(select(func.count()).select_from(Order).where(Order.code.like(like))).scalar_one()
    return f"ORD-{today}-{(n + 1):04d}"


@router.post("", response_model=OrderOut, status_code=201)
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    order = Order(
        code=payload.code or _make_order_code(db),
        pickup_x=payload.pickup_location.x,
        pickup_y=payload.pickup_location.y,
        dropoff_x=payload.dropoff_location.x,
        dropoff_y=payload.dropoff_location.y,
        priority=payload.priority,
        status="CREATED",
        created_at=_now(),
        updated_at=_now(),
    )
    db.add(order)
    try:
        db.flush()
        log_event(db, "ORDER_CREATED", message=f"Order {order.code} created", order_id=order.id)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Order code already exists")
    db.refresh(order)
    return order


@router.get("", response_model=list[OrderOut])
def list_orders(
    status: str | None = Query(default=None),
    priority: int | None = Query(default=None, ge=1, le=10),
    db: Session = Depends(get_db),
):
    stmt = select(Order).order_by(Order.created_at.desc())
    if status:
        stmt = stmt.where(Order.status == status)
    if priority is not None:
        stmt = stmt.where(Order.priority == priority)
    return db.execute(stmt).scalars().all()


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: UUID, db: Session = Depends(get_db)):
    order = db.execute(select(Order).where(Order.id == order_id)).scalars().first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.patch("/{order_id}", response_model=OrderOut)
def update_order(order_id: UUID, payload: OrderUpdate, db: Session = Depends(get_db)):
    order = db.execute(select(Order).where(Order.id == order_id)).scalars().first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if payload.priority is not None:
        order.priority = payload.priority

    if payload.status is not None:
        if payload.status == "CANCELED" and order.status in ("COMPLETED", "FAILED"):
            raise HTTPException(status_code=400, detail="Cannot cancel a completed/failed order")
        order.status = payload.status
        log_event(
            db,
            "ORDER_STATUS_CHANGED",
            message=f"Order {order.code} status -> {order.status}",
            order_id=order.id,
        )

    if payload.priority is not None:
        log_event(
            db,
            "ORDER_PRIORITY_UPDATED",
            message=f"Order {order.code} priority -> {order.priority}",
            order_id=order.id,
        )

    order.updated_at = _now()
    db.commit()
    db.refresh(order)
    return order
