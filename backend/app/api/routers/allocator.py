from datetime import datetime, timezone
from math import sqrt
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_db
from app.models.allocator_run import AllocatorRun
from app.models.allocator_run_item import AllocatorRunItem
from app.models.mission import Mission
from app.models.mission_step import MissionStep
from app.models.order import Order
from app.models.robot import Robot
from app.schemas.allocator import (
    AllocationAssigned,
    AllocationSummary,
    AllocationUnassigned,
    AllocatorRunDetailOut,
    AllocatorRunRequest,
    AllocatorRunResponse,
)
from app.services.simulator import start_mission_simulation

router = APIRouter(prefix="/allocator", tags=["allocator"])


def _now():
    return datetime.now(timezone.utc)


def _distance(rx: float, ry: float, ox: float, oy: float) -> float:
    return sqrt((rx - ox) ** 2 + (ry - oy) ** 2)


def _score(distance: float, battery_pct: int, priority: int) -> float:
    return distance - (priority * 0.2) + ((100 - battery_pct) * 0.01)


def _make_mission_code(db: Session) -> str:
    today = _now().strftime("%Y%m%d")
    like = f"MIS-{today}-%"
    n = db.execute(select(func.count()).select_from(Mission).where(Mission.code.like(like))).scalar_one()
    return f"MIS-{today}-{(n + 1):04d}"


@router.post("/run", response_model=AllocatorRunResponse)
def run_allocator(payload: AllocatorRunRequest, db: Session = Depends(get_db)):
    orders = db.execute(
        select(Order)
        .where(Order.status == "CREATED")
        .order_by(Order.priority.desc(), Order.created_at.asc())
        .limit(payload.max_orders)
    ).scalars().all()

    available_robots = db.execute(
        select(Robot)
        .where(Robot.status == "IDLE")
        .where(Robot.battery_pct >= payload.battery_min_pct)
        .order_by(Robot.updated_at.asc())
    ).scalars().all()

    run = AllocatorRun(
        status="DONE",
        battery_min_pct=payload.battery_min_pct,
        max_orders=payload.max_orders,
        total_orders=len(orders),
        assigned_count=0,
        unassigned_count=0,
        created_at=_now(),
    )
    db.add(run)
    db.flush()

    assigned: list[AllocationAssigned] = []
    unassigned: list[AllocationUnassigned] = []
    missions_to_start: list[UUID] = []

    robot_pool = list(available_robots)

    for order in orders:
        if not robot_pool:
            run_item = AllocatorRunItem(
                run_id=run.id,
                order_id=order.id,
                robot_id=None,
                mission_id=None,
                result="UNASSIGNED",
                reason="NO_IDLE_ROBOT",
                score=None,
                distance=None,
                created_at=_now(),
            )
            db.add(run_item)
            unassigned.append(AllocationUnassigned(order_id=order.id, reason="NO_IDLE_ROBOT"))
            continue

        best_idx = -1
        best_score = None
        best_distance = None

        for i, robot in enumerate(robot_pool):
            dist = _distance(robot.last_pose_x, robot.last_pose_y, order.pickup_x, order.pickup_y)
            sc = _score(dist, robot.battery_pct, order.priority)
            if best_score is None or sc < best_score:
                best_idx = i
                best_score = sc
                best_distance = dist

        if best_idx < 0 or best_score is None or best_distance is None:
            run_item = AllocatorRunItem(
                run_id=run.id,
                order_id=order.id,
                robot_id=None,
                mission_id=None,
                result="UNASSIGNED",
                reason="NO_ELIGIBLE_ROBOT",
                score=None,
                distance=None,
                created_at=_now(),
            )
            db.add(run_item)
            unassigned.append(AllocationUnassigned(order_id=order.id, reason="NO_ELIGIBLE_ROBOT"))
            continue

        robot = robot_pool.pop(best_idx)
        mission = Mission(
            code=_make_mission_code(db),
            mission_type="MOVE",
            status="ASSIGNED",
            priority=order.priority,
            order_id=order.id,
            assigned_robot_id=robot.id,
            progress_pct=0,
            created_at=_now(),
            updated_at=_now(),
        )
        db.add(mission)
        db.flush()

        db.add_all(
            [
                MissionStep(
                    mission_id=mission.id,
                    seq=1,
                    action=f"PICKUP at ({order.pickup_x:.2f}, {order.pickup_y:.2f})",
                    status="PENDING",
                    created_at=_now(),
                    updated_at=_now(),
                ),
                MissionStep(
                    mission_id=mission.id,
                    seq=2,
                    action=f"DROPOFF at ({order.dropoff_x:.2f}, {order.dropoff_y:.2f})",
                    status="PENDING",
                    created_at=_now(),
                    updated_at=_now(),
                ),
            ]
        )

        robot.status = "BUSY"
        robot.updated_at = _now()
        robot.last_seen_at = _now()

        order.status = "RUNNING"
        if not order.started_at:
            order.started_at = _now()
        order.updated_at = _now()

        db.add(
            AllocatorRunItem(
                run_id=run.id,
                order_id=order.id,
                robot_id=robot.id,
                mission_id=mission.id,
                result="ASSIGNED",
                reason=None,
                score=best_score,
                distance=best_distance,
                created_at=_now(),
            )
        )

        assigned.append(
            AllocationAssigned(
                order_id=order.id,
                mission_id=mission.id,
                robot_id=robot.id,
                score=best_score,
                distance=best_distance,
            )
        )
        missions_to_start.append(mission.id)

    run.assigned_count = len(assigned)
    run.unassigned_count = len(unassigned)
    run.completed_at = _now()

    db.commit()

    for mission_id in missions_to_start:
        start_mission_simulation(mission_id)

    return AllocatorRunResponse(
        run_id=run.id,
        assigned=assigned,
        unassigned=unassigned,
        summary=AllocationSummary(total=len(orders), assigned=len(assigned), unassigned=len(unassigned)),
    )


@router.get("/runs/{run_id}", response_model=AllocatorRunDetailOut)
def get_allocator_run(run_id: UUID, db: Session = Depends(get_db)):
    run = db.execute(
        select(AllocatorRun).options(selectinload(AllocatorRun.items)).where(AllocatorRun.id == run_id)
    ).scalars().first()
    if not run:
        raise HTTPException(status_code=404, detail="Allocator run not found")
    return run
