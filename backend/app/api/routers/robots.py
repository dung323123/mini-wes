from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api.deps import get_db
from app.models.mission import Mission
from app.models.robot import Robot
from app.schemas.robot import RobotOut, RobotDetailOut, RobotMissionSummary

router = APIRouter(prefix="/robots", tags=["robots"])


@router.get("", response_model=list[RobotOut])
def list_robots(
    status: str | None = Query(default=None),
    type: str | None = Query(default=None, alias="type"),
    db: Session = Depends(get_db),
):
    stmt = select(Robot).order_by(Robot.name.asc())
    if status:
        stmt = stmt.where(Robot.status == status)
    if type:
        stmt = stmt.where(Robot.robot_type == type)
    robots = db.execute(stmt).scalars().all()
    return robots


@router.get("/{robot_id}", response_model=RobotDetailOut)
def get_robot(robot_id: UUID, include_mission: bool = Query(default=True), db: Session = Depends(get_db)):
    robot = db.execute(select(Robot).where(Robot.id == robot_id)).scalars().first()
    if not robot:
        raise HTTPException(status_code=404, detail="Robot not found")

    active_mission = None
    if include_mission:
        active_mission = db.execute(
            select(Mission)
            .where(Mission.assigned_robot_id == robot.id)
            .where(Mission.status.in_(("ASSIGNED", "RUNNING")))
            .order_by(Mission.updated_at.desc())
        ).scalars().first()

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
