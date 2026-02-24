from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.mission import Mission
from app.models.order import Order
from app.models.robot import Robot
from app.schemas.dashboard import CountItem, DashboardSummaryOut, FleetRobotItem

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummaryOut)
def get_dashboard_summary(db: Session = Depends(get_db)):
    robots_total = db.execute(select(func.count()).select_from(Robot)).scalar_one()

    robot_rows = db.execute(select(Robot.status, func.count()).group_by(Robot.status)).all()
    order_rows = db.execute(select(Order.status, func.count()).group_by(Order.status)).all()
    task_rows = db.execute(select(Mission.status, func.count()).group_by(Mission.status)).all()

    robots_by_status = [CountItem(key=row[0], count=row[1]) for row in robot_rows]
    orders_by_status = [CountItem(key=row[0], count=row[1]) for row in order_rows]
    tasks_by_status = [CountItem(key=row[0], count=row[1]) for row in task_rows]

    tasks_running = db.execute(
        select(func.count()).select_from(Mission).where(Mission.status.in_(("ASSIGNED", "RUNNING")))
    ).scalar_one()

    return DashboardSummaryOut(
        robots_total=robots_total,
        robots_by_status=robots_by_status,
        orders_by_status=orders_by_status,
        tasks_by_status=tasks_by_status,
        tasks_running=tasks_running,
    )


@router.get("/fleet", response_model=list[FleetRobotItem])
def get_dashboard_fleet(db: Session = Depends(get_db)):
    robots = db.execute(select(Robot).order_by(Robot.name.asc())).scalars().all()
    out: list[FleetRobotItem] = []
    for robot in robots:
        mission = db.execute(
            select(Mission)
            .where(Mission.assigned_robot_id == robot.id)
            .where(Mission.status.in_(("ASSIGNED", "RUNNING")))
            .order_by(Mission.updated_at.desc())
            .limit(1)
        ).scalars().first()
        out.append(
            FleetRobotItem(
                robot_id=robot.id,
                name=robot.name,
                robot_type=robot.robot_type,
                status=robot.status,
                battery_pct=robot.battery_pct,
                x=robot.last_pose_x,
                y=robot.last_pose_y,
                theta=robot.last_pose_theta,
                last_seen_at=robot.last_seen_at,
                active_task_id=mission.id if mission else None,
                active_task_code=mission.code if mission else None,
                active_task_status=mission.status if mission else None,
            )
        )
    return out
