import random
import threading
import time
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select

from app.core.db import SessionLocal
from app.models.mission import Mission
from app.models.mission_step import MissionStep
from app.models.robot import Robot


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

        # mission phải có robot
        if not mission.assigned_robot_id:
            return

        robot = db.execute(select(Robot).where(Robot.id == mission.assigned_robot_id)).scalars().first()
        if not robot:
            return

        steps = db.execute(
            select(MissionStep).where(MissionStep.mission_id == mission.id).order_by(MissionStep.seq.asc())
        ).scalars().all()

        # chuyển RUNNING
        mission.status = "RUNNING"
        mission.started_at = _now()
        mission.updated_at = _now()
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
            db.commit()

            time.sleep(random.uniform(1.0, 2.5))

            # update robot telemetry “giả”
            robot.battery_pct = max(0, robot.battery_pct - random.randint(0, 2))
            robot.last_pose_x += random.uniform(-0.5, 0.8)
            robot.last_pose_y += random.uniform(-0.5, 0.8)
            robot.last_pose_theta += random.uniform(-0.2, 0.2)
            robot.last_seen_at = _now()
            robot.updated_at = _now()

            if fail:
                step.status = "FAILED"
                step.finished_at = _now()
                step.updated_at = _now()

                mission.status = "FAILED"
                mission.finished_at = _now()
                mission.updated_at = _now()

                robot.status = "ERROR"
                robot.updated_at = _now()

                db.commit()
                return

            step.status = "DONE"
            step.finished_at = _now()
            step.updated_at = _now()

            done += 1
            mission.progress_pct = int(done * 100 / total)
            mission.updated_at = _now()
            db.commit()

        # complete
        mission.progress_pct = 100
        mission.status = "COMPLETED"
        mission.finished_at = _now()
        mission.updated_at = _now()

        robot.status = "IDLE"
        robot.updated_at = _now()

        db.commit()
    finally:
        db.close()