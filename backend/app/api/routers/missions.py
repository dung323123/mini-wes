from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_db
from app.models.mission import Mission
from app.models.mission_step import MissionStep
from app.models.order import Order
from app.models.robot import Robot
from app.schemas.mission import MissionOut, MissionCreate, MissionAssign, MissionDetailOut
from app.services.events import log_event
from app.services.simulator import start_mission_simulation

router = APIRouter(prefix="/missions", tags=["missions"])


def _now():
    return datetime.now(timezone.utc)


def _make_mission_code(db: Session) -> str:
    # MIS-YYYYMMDD-0001 (đếm theo ngày, đủ dùng MVP)
    today = _now().strftime("%Y%m%d")
    like = f"MIS-{today}-%"
    n = db.execute(select(func.count()).select_from(Mission).where(Mission.code.like(like))).scalar_one()
    return f"MIS-{today}-{(n + 1):04d}"


@router.get("", response_model=list[MissionOut])
def list_missions(
    status: str | None = Query(default=None),
    robot_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
):
    stmt = select(Mission).options(selectinload(Mission.steps)).order_by(Mission.created_at.desc())
    if status:
        stmt = stmt.where(Mission.status == status)
    if robot_id:
        stmt = stmt.where(Mission.assigned_robot_id == robot_id)
    missions = db.execute(stmt).scalars().all()
    return missions


@router.get("/{mission_id}", response_model=MissionDetailOut)
def get_mission(mission_id: UUID, db: Session = Depends(get_db)):
    mission = db.execute(
        select(Mission).options(selectinload(Mission.steps)).where(Mission.id == mission_id)
    ).scalars().first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    return mission


@router.post("", response_model=MissionOut, status_code=201)
def create_mission(payload: MissionCreate, db: Session = Depends(get_db)):
    if payload.order_id:
        order = db.execute(select(Order).where(Order.id == payload.order_id)).scalars().first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

    code = _make_mission_code(db)

    m = Mission(
        code=code,
        mission_type=payload.mission_type,
        status="CREATED",
        priority=payload.priority,
        order_id=payload.order_id,
        assigned_robot_id=None,
        progress_pct=0,
        created_at=_now(),
        updated_at=_now(),
    )

    db.add(m)
    db.flush()  # để có m.id

    steps = []
    for s in payload.steps:
        steps.append(
            MissionStep(
                mission_id=m.id,
                seq=s.seq,
                action=s.action,
                status="PENDING",
                created_at=_now(),
                updated_at=_now(),
            )
        )

    db.add_all(steps)
    log_event(
        db,
        "MISSION_CREATED",
        message=f"Mission {m.code} created",
        mission_id=m.id,
        order_id=m.order_id,
    )
    db.commit()

    # reload để có relationship steps
    m = db.execute(
        select(Mission).options(selectinload(Mission.steps)).where(Mission.id == m.id)
    ).scalars().first()
    return m


@router.post("/{mission_id}/assign", response_model=MissionOut)
def assign_mission(mission_id: UUID, payload: MissionAssign, db: Session = Depends(get_db)):
    mission = db.execute(select(Mission).where(Mission.id == mission_id)).scalars().first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    if mission.status not in ("CREATED",):
        raise HTTPException(status_code=400, detail=f"Mission not assignable from status={mission.status}")

    robot = db.execute(select(Robot).where(Robot.id == payload.robot_id)).scalars().first()
    if not robot:
        raise HTTPException(status_code=404, detail="Robot not found")

    if robot.status != "IDLE":
        raise HTTPException(status_code=400, detail=f"Robot not available (status={robot.status})")

    # gán
    mission.assigned_robot_id = robot.id
    mission.status = "ASSIGNED"
    mission.progress_pct = 0
    mission.updated_at = _now()

    robot.status = "BUSY"
    robot.updated_at = _now()
    robot.last_seen_at = _now()
    if mission.order_id:
        order = db.execute(select(Order).where(Order.id == mission.order_id)).scalars().first()
        if order:
            order.status = "RUNNING"
            if not order.started_at:
                order.started_at = _now()
            order.updated_at = _now()
            log_event(
                db,
                "ORDER_STATUS_CHANGED",
                message=f"Order {order.code} status -> RUNNING",
                order_id=order.id,
                mission_id=mission.id,
                robot_id=robot.id,
            )

    log_event(
        db,
        "MISSION_ASSIGNED",
        message=f"Mission {mission.code} assigned to robot {robot.name}",
        mission_id=mission.id,
        robot_id=robot.id,
        order_id=mission.order_id,
    )

    db.commit()

    # start simulator async (thread)
    start_mission_simulation(mission.id)

    # reload
    mission = db.execute(
        select(Mission).options(selectinload(Mission.steps)).where(Mission.id == mission.id)
    ).scalars().first()
    return mission
