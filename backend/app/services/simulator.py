import random
import threading
import time
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select

from app.core.db import SessionLocal
from app.models.mission import Mission
from app.models.mission_step import MissionStep
from app.models.order import Order
from app.models.robot import Robot
from app.models.telemetry import Telemetry
from app.services.events import log_event


def _now():
    return datetime.now(timezone.utc)


def start_mission_simulation(mission_id: UUID) -> None:
    t = threading.Thread(target=_run_mission, args=(mission_id,), daemon=True)
    t.start()


def _run_mission(mission_id: UUID) -> None:
    db = SessionLocal()
    try:
        mission = db.execute(select(Mission).where(Mission.id == mission_id)).scalars().first()
        if not mission:
            return
        order = None
        if mission.order_id:
            order = db.execute(select(Order).where(Order.id == mission.order_id)).scalars().first()

        # mission phải có robot
        if not mission.assigned_robot_id:
            return

        robot = db.execute(select(Robot).where(Robot.id == mission.assigned_robot_id)).scalars().first()
        if not robot:
            return

        db.add(
            Telemetry(
                robot_id=robot.id,
                x=robot.last_pose_x,
                y=robot.last_pose_y,
                theta=robot.last_pose_theta,
                battery_pct=robot.battery_pct,
                recorded_at=_now(),
                created_at=_now(),
            )
        )
        db.commit()

        steps = db.execute(
            select(MissionStep).where(MissionStep.mission_id == mission.id).order_by(MissionStep.seq.asc())
        ).scalars().all()

        # chuyển RUNNING
        mission.status = "RUNNING"
        mission.started_at = _now()
        mission.updated_at = _now()
        log_event(
            db,
            "MISSION_RUNNING",
            message=f"Mission {mission.code} is running",
            mission_id=mission.id,
            robot_id=robot.id,
            order_id=mission.order_id,
        )
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
        db.commit()

        total = max(len(steps), 1)
        done = 0

        for step in steps:
            # random fail rất nhỏ để demo
            fail = (random.random() < 0.05)

            step.status = "RUNNING"
            step.started_at = _now()
            step.updated_at = _now()
            mission.updated_at = _now()
            log_event(
                db,
                "STEP_RUNNING",
                message=f"Mission {mission.code} step {step.seq} running",
                mission_id=mission.id,
                robot_id=robot.id,
                order_id=mission.order_id,
            )
            db.commit()

            time.sleep(random.uniform(1.0, 2.5))

            # update robot telemetry “giả”
            robot.battery_pct = max(0, robot.battery_pct - random.randint(0, 2))
            robot.last_pose_x += random.uniform(-0.5, 0.8)
            robot.last_pose_y += random.uniform(-0.5, 0.8)
            robot.last_pose_theta += random.uniform(-0.2, 0.2)
            robot.last_seen_at = _now()
            robot.updated_at = _now()
            db.add(
                Telemetry(
                    robot_id=robot.id,
                    x=robot.last_pose_x,
                    y=robot.last_pose_y,
                    theta=robot.last_pose_theta,
                    battery_pct=robot.battery_pct,
                    recorded_at=_now(),
                    created_at=_now(),
                )
            )

            if fail:
                step.status = "FAILED"
                step.finished_at = _now()
                step.updated_at = _now()

                mission.status = "FAILED"
                mission.finished_at = _now()
                mission.updated_at = _now()
                log_event(
                    db,
                    "MISSION_FAILED",
                    message=f"Mission {mission.code} failed at step {step.seq}",
                    mission_id=mission.id,
                    robot_id=robot.id,
                    order_id=mission.order_id,
                )
                if order:
                    order.status = "FAILED"
                    order.finished_at = _now()
                    order.updated_at = _now()
                    log_event(
                        db,
                        "ORDER_STATUS_CHANGED",
                        message=f"Order {order.code} status -> FAILED",
                        order_id=order.id,
                        mission_id=mission.id,
                        robot_id=robot.id,
                    )

                robot.status = "ERROR"
                robot.updated_at = _now()

                db.commit()
                return

            step.status = "DONE"
            step.finished_at = _now()
            step.updated_at = _now()
            log_event(
                db,
                "STEP_DONE",
                message=f"Mission {mission.code} step {step.seq} done",
                mission_id=mission.id,
                robot_id=robot.id,
                order_id=mission.order_id,
            )

            done += 1
            mission.progress_pct = int(done * 100 / total)
            mission.updated_at = _now()
            db.commit()

        # complete
        mission.progress_pct = 100
        mission.status = "COMPLETED"
        mission.finished_at = _now()
        mission.updated_at = _now()
        log_event(
            db,
            "MISSION_COMPLETED",
            message=f"Mission {mission.code} completed",
            mission_id=mission.id,
            robot_id=robot.id,
            order_id=mission.order_id,
        )
        if order:
            order.status = "COMPLETED"
            order.finished_at = _now()
            order.updated_at = _now()
            log_event(
                db,
                "ORDER_STATUS_CHANGED",
                message=f"Order {order.code} status -> COMPLETED",
                order_id=order.id,
                mission_id=mission.id,
                robot_id=robot.id,
            )

        robot.status = "IDLE"
        robot.updated_at = _now()

        db.commit()
    finally:
        db.close()
