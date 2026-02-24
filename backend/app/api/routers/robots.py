from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api.deps import get_db
from app.models.robot import Robot
from app.schemas.robot import RobotOut, Pose

router = APIRouter(prefix="/robots", tags=["robots"])


@router.get("", response_model=list[RobotOut])
def list_robots(db: Session = Depends(get_db)):
    robots = db.execute(select(Robot).order_by(Robot.name.asc())).scalars().all()
    # map ORM -> API schema (compose last_pose)
    out: list[RobotOut] = []
    for r in robots:
        out.append(
            RobotOut(
                id=r.id,
                name=r.name,
                robot_type=r.robot_type,
                status=r.status,
                battery_pct=r.battery_pct,
                last_pose=Pose(x=r.last_pose_x, y=r.last_pose_y, theta=r.last_pose_theta),
                last_seen_at=r.last_seen_at,
            )
        )
    return out