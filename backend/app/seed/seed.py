import random
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.db import SessionLocal
from app.models.robot import Robot
from app.models.mission import Mission


def make_mission_code(i: int) -> str:
    # MIS-YYYYMMDD-0001
    d = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"MIS-{d}-{i:04d}"


def run_seed():
    db = SessionLocal()
    try:
        # idempotent-ish: if already seeded, skip
        existing = db.execute(select(Robot).limit(1)).scalars().first()
        if existing:
            print("Seed skipped: robots already exist.")
            return

        robots = []
        for i in range(1, 7):
            robots.append(Robot(name=f"AMR-{i:02d}", robot_type="AMR", status="IDLE", battery_pct=random.randint(70, 100)))
        for i in range(1, 3):
            robots.append(Robot(name=f"ARM-{i:02d}", robot_type="MANIPULATOR", status="IDLE", battery_pct=random.randint(70, 100)))
        for i in range(1, 3):
            robots.append(Robot(name=f"HUM-{i:02d}", robot_type="HUMANOID", status="IDLE", battery_pct=random.randint(70, 100)))

        db.add_all(robots)
        db.flush()  # assign ids

        mission_types = ["MOVE", "PICK", "DOCK", "PATROL"]
        missions = []
        for i in range(1, 11):
            missions.append(
                Mission(
                    code=make_mission_code(i),
                    mission_type=random.choice(mission_types),
                    status="CREATED",
                    priority=random.randint(1, 10),
                    assigned_robot_id=None,
                    progress_pct=0,
                )
            )
        db.add_all(missions)
        db.commit()
        print("Seed done.")
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()