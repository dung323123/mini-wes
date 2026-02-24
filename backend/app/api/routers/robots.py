from uuid import UUID
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.api.deps import get_db
from app.models.mission import Mission
from app.models.robot import Robot
from app.schemas.robot import RobotOut, RobotDetailOut, RobotMissionSummary, RobotCreate, RobotUpdate
from app.services.events import log_event

router = APIRouter(prefix="/robots", tags=["robots"])


def _now():
    return datetime.now(timezone.utc)


def _get_active_mission(db: Session, robot_id: UUID):
    return db.execute(
        select(Mission)
        .where(Mission.assigned_robot_id == robot_id)
        .where(Mission.status.in_(("ASSIGNED", "RUNNING")))
        .order_by(Mission.updated_at.desc())
    ).scalars().first()


@router.get("", response_model=list[RobotOut])
def list_robots(
    status: str | None = Query(default=None),
    type: str | None = Query(default=None, alias="type"),
    enabled: bool | None = Query(default=None),
    db: Session = Depends(get_db),
):
    stmt = select(Robot).order_by(Robot.name.asc())
    if status:
        stmt = stmt.where(Robot.status == status)
    if type:
        stmt = stmt.where(Robot.robot_type == type)
    if enabled is True:
        stmt = stmt.where(Robot.status != "DISABLED")
    if enabled is False:
        stmt = stmt.where(Robot.status == "DISABLED")
    robots = db.execute(stmt).scalars().all()
    return robots


@router.post("", response_model=RobotOut, status_code=201)
def create_robot(payload: RobotCreate, db: Session = Depends(get_db)):
    robot = Robot(
        name=payload.name,
        robot_type=payload.robot_type,
        status=payload.status,
        battery_pct=payload.battery_pct,
        last_pose_x=payload.last_pose_x,
        last_pose_y=payload.last_pose_y,
        last_pose_theta=payload.last_pose_theta,
        last_seen_at=_now(),
        created_at=_now(),
        updated_at=_now(),
    )
    db.add(robot)
    try:
        db.flush()
        log_event(db, "ROBOT_REGISTERED", message=f"Robot {robot.name} registered", robot_id=robot.id)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Robot name already exists")
    db.refresh(robot)
    return robot


@router.get("/{robot_id}", response_model=RobotDetailOut)
def get_robot(robot_id: UUID, include_mission: bool = Query(default=True), db: Session = Depends(get_db)):
    robot = db.execute(select(Robot).where(Robot.id == robot_id)).scalars().first()
    if not robot:
        raise HTTPException(status_code=404, detail="Robot not found")

    active_mission = None
    if include_mission:
        active_mission = _get_active_mission(db, robot.id)

    return RobotDetailOut(
        id=robot.id,
        name=robot.name,
        robot_type=robot.robot_type,
        status=robot.status,
        battery_pct=robot.battery_pct,
        last_pose_x=robot.last_pose_x,
        last_pose_y=robot.last_pose_y,
        last_pose_theta=robot.last_pose_theta,
        last_seen_at=robot.last_seen_at,
        created_at=robot.created_at,
        updated_at=robot.updated_at,
        active_mission=RobotMissionSummary.model_validate(active_mission) if active_mission else None,
    )


@router.patch("/{robot_id}", response_model=RobotOut)
def update_robot(robot_id: UUID, payload: RobotUpdate, db: Session = Depends(get_db)):
    robot = db.execute(select(Robot).where(Robot.id == robot_id)).scalars().first()
    if not robot:
        raise HTTPException(status_code=404, detail="Robot not found")

    active_mission = _get_active_mission(db, robot.id)

    if payload.enabled is False and active_mission:
        raise HTTPException(status_code=400, detail="Cannot disable robot with active mission")

    if payload.name is not None:
        robot.name = payload.name
    if payload.robot_type is not None:
        robot.robot_type = payload.robot_type
    if payload.battery_pct is not None:
        robot.battery_pct = payload.battery_pct
    if payload.last_pose_x is not None:
        robot.last_pose_x = payload.last_pose_x
    if payload.last_pose_y is not None:
        robot.last_pose_y = payload.last_pose_y
    if payload.last_pose_theta is not None:
        robot.last_pose_theta = payload.last_pose_theta

    if payload.enabled is False:
        robot.status = "DISABLED"
    elif payload.enabled is True and robot.status == "DISABLED" and payload.status is None:
        robot.status = "IDLE"

    if payload.status is not None:
        if payload.status == "DISABLED" and active_mission:
            raise HTTPException(status_code=400, detail="Cannot set DISABLED while mission is active")
        robot.status = payload.status

    robot.updated_at = _now()
    if any(v is not None for v in (payload.last_pose_x, payload.last_pose_y, payload.last_pose_theta, payload.battery_pct)):
        robot.last_seen_at = _now()

    log_event(
        db,
        "ROBOT_UPDATED",
        message=f"Robot {robot.name} updated (status={robot.status})",
        robot_id=robot.id,
    )

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Robot name already exists")
    db.refresh(robot)
    return robot
