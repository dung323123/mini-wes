import argparse
import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import text

from app.core.db import SessionLocal
from app.models.event import Event
from app.models.mission import Mission
from app.models.mission_step import MissionStep
from app.models.order import Order
from app.models.robot import Robot
from app.models.telemetry import Telemetry


def _now():
    return datetime.now(timezone.utc)


def _mission_code(i: int) -> str:
    d = _now().strftime("%Y%m%d")
    return f"MIS-{d}-{i:04d}"


def _order_code(i: int) -> str:
    d = _now().strftime("%Y%m%d")
    return f"ORD-{d}-{i:04d}"


def _reset_all(db) -> None:
    db.execute(
        text(
            """
            TRUNCATE TABLE
              allocator_run_items,
              allocator_runs,
              telemetry,
              events,
              mission_steps,
              missions,
              orders,
              robots
            RESTART IDENTITY CASCADE
            """
        )
    )
    db.commit()


def run_seed(reset: bool = True) -> None:
    rng = random.Random(20260224)
    db = SessionLocal()
    try:
        if reset:
            _reset_all(db)

        base_time = _now()

        robots = [
            Robot(name="AMR-01", robot_type="AMR", status="IDLE", battery_pct=94, last_pose_x=2.1, last_pose_y=1.4, last_pose_theta=0.1),
            Robot(name="AMR-02", robot_type="AMR", status="IDLE", battery_pct=88, last_pose_x=4.8, last_pose_y=3.2, last_pose_theta=-0.1),
            Robot(name="AMR-03", robot_type="AMR", status="BUSY", battery_pct=72, last_pose_x=8.5, last_pose_y=5.1, last_pose_theta=0.3),
            Robot(name="AMR-04", robot_type="AMR", status="BUSY", battery_pct=67, last_pose_x=10.0, last_pose_y=2.9, last_pose_theta=-0.2),
            Robot(name="AMR-05", robot_type="AMR", status="CHARGING", battery_pct=31, last_pose_x=1.2, last_pose_y=8.9, last_pose_theta=0.0),
            Robot(name="AMR-06", robot_type="AMR", status="IDLE", battery_pct=91, last_pose_x=6.8, last_pose_y=8.3, last_pose_theta=0.2),
            Robot(name="AMR-07", robot_type="AMR", status="DISABLED", battery_pct=77, last_pose_x=11.3, last_pose_y=10.1, last_pose_theta=0.0),
            Robot(name="AMR-08", robot_type="AMR", status="ERROR", battery_pct=49, last_pose_x=9.4, last_pose_y=11.5, last_pose_theta=-0.4),
            Robot(name="ARM-01", robot_type="MANIPULATOR", status="IDLE", battery_pct=95, last_pose_x=3.3, last_pose_y=12.1, last_pose_theta=0.0),
            Robot(name="ARM-02", robot_type="MANIPULATOR", status="IDLE", battery_pct=92, last_pose_x=5.5, last_pose_y=13.2, last_pose_theta=0.0),
            Robot(name="HUM-01", robot_type="HUMANOID", status="IDLE", battery_pct=86, last_pose_x=7.1, last_pose_y=9.9, last_pose_theta=0.6),
            Robot(name="HUM-02", robot_type="HUMANOID", status="IDLE", battery_pct=90, last_pose_x=12.7, last_pose_y=6.6, last_pose_theta=-0.3),
        ]

        for r in robots:
            r.created_at = base_time - timedelta(days=rng.randint(1, 7))
            r.updated_at = base_time - timedelta(minutes=rng.randint(1, 30))
            r.last_seen_at = base_time - timedelta(minutes=rng.randint(0, 12))

        db.add_all(robots)
        db.flush()

        orders: list[Order] = []
        statuses = (
            ["CREATED"] * 6
            + ["RUNNING"] * 2
            + ["COMPLETED"] * 3
            + ["FAILED"]
            + ["CANCELED"]
        )
        rng.shuffle(statuses)
        for i, status in enumerate(statuses, start=1):
            order = Order(
                code=_order_code(i),
                pickup_x=round(rng.uniform(1.0, 14.0), 2),
                pickup_y=round(rng.uniform(1.0, 14.0), 2),
                dropoff_x=round(rng.uniform(1.0, 14.0), 2),
                dropoff_y=round(rng.uniform(1.0, 14.0), 2),
                priority=rng.randint(1, 10),
                status=status,
                created_at=base_time - timedelta(hours=rng.randint(4, 36)),
                updated_at=base_time - timedelta(minutes=rng.randint(1, 120)),
            )
            if status in ("RUNNING", "COMPLETED", "FAILED"):
                order.started_at = order.created_at + timedelta(minutes=rng.randint(2, 20))
            if status in ("COMPLETED", "FAILED"):
                order.finished_at = order.started_at + timedelta(minutes=rng.randint(8, 30))
            orders.append(order)
        db.add_all(orders)
        db.flush()

        running_orders = [o for o in orders if o.status == "RUNNING"][:2]
        completed_orders = [o for o in orders if o.status == "COMPLETED"][:3]
        failed_orders = [o for o in orders if o.status == "FAILED"][:1]
        created_orders = [o for o in orders if o.status == "CREATED"][:4]

        missions: list[Mission] = []
        mission_idx = 1

        for order, robot in zip(running_orders, [robots[2], robots[3]]):
            mission = Mission(
                code=_mission_code(mission_idx),
                mission_type="MOVE",
                status="RUNNING",
                priority=order.priority,
                order_id=order.id,
                assigned_robot_id=robot.id,
                progress_pct=rng.randint(30, 80),
                started_at=order.started_at,
                created_at=order.created_at + timedelta(minutes=1),
                updated_at=base_time - timedelta(minutes=rng.randint(1, 8)),
            )
            missions.append(mission)
            mission_idx += 1

        for order in completed_orders:
            mission = Mission(
                code=_mission_code(mission_idx),
                mission_type=rng.choice(["MOVE", "PICK", "DOCK", "PATROL"]),
                status="COMPLETED",
                priority=order.priority,
                order_id=order.id,
                assigned_robot_id=rng.choice([robots[0], robots[1], robots[5], robots[8], robots[9]]).id,
                progress_pct=100,
                started_at=order.started_at,
                finished_at=order.finished_at,
                created_at=order.created_at + timedelta(minutes=1),
                updated_at=order.finished_at or base_time,
            )
            missions.append(mission)
            mission_idx += 1

        for order in failed_orders:
            mission = Mission(
                code=_mission_code(mission_idx),
                mission_type="MOVE",
                status="FAILED",
                priority=order.priority,
                order_id=order.id,
                assigned_robot_id=robots[7].id,
                progress_pct=rng.randint(10, 60),
                started_at=order.started_at,
                finished_at=order.finished_at,
                created_at=order.created_at + timedelta(minutes=1),
                updated_at=order.finished_at or base_time,
            )
            missions.append(mission)
            mission_idx += 1

        for order in created_orders:
            mission = Mission(
                code=_mission_code(mission_idx),
                mission_type=rng.choice(["MOVE", "PICK", "DOCK", "PATROL"]),
                status="CREATED",
                priority=order.priority,
                order_id=order.id,
                assigned_robot_id=None,
                progress_pct=0,
                created_at=order.created_at + timedelta(minutes=1),
                updated_at=base_time - timedelta(minutes=rng.randint(20, 120)),
            )
            missions.append(mission)
            mission_idx += 1

        db.add_all(missions)
        db.flush()

        steps: list[MissionStep] = []
        for m in missions:
            status1 = "PENDING"
            status2 = "PENDING"
            started1 = None
            started2 = None
            finished1 = None
            finished2 = None

            if m.status == "RUNNING":
                status1, status2 = "DONE", "RUNNING"
                started1 = m.started_at
                finished1 = m.started_at + timedelta(minutes=3) if m.started_at else None
                started2 = m.started_at + timedelta(minutes=4) if m.started_at else None
            elif m.status == "COMPLETED":
                status1, status2 = "DONE", "DONE"
                started1 = m.started_at
                finished1 = m.started_at + timedelta(minutes=3) if m.started_at else None
                started2 = m.started_at + timedelta(minutes=4) if m.started_at else None
                finished2 = m.finished_at
            elif m.status == "FAILED":
                status1, status2 = "DONE", "FAILED"
                started1 = m.started_at
                finished1 = m.started_at + timedelta(minutes=3) if m.started_at else None
                started2 = m.started_at + timedelta(minutes=4) if m.started_at else None
                finished2 = m.finished_at

            steps.append(
                MissionStep(
                    mission_id=m.id,
                    seq=1,
                    action="PICKUP",
                    status=status1,
                    started_at=started1,
                    finished_at=finished1,
                    created_at=m.created_at,
                    updated_at=m.updated_at,
                )
            )
            steps.append(
                MissionStep(
                    mission_id=m.id,
                    seq=2,
                    action="DROPOFF",
                    status=status2,
                    started_at=started2,
                    finished_at=finished2,
                    created_at=m.created_at,
                    updated_at=m.updated_at,
                )
            )
        db.add_all(steps)

        telemetry_rows: list[Telemetry] = []
        for robot in robots:
            base_x = robot.last_pose_x
            base_y = robot.last_pose_y
            base_theta = robot.last_pose_theta
            base_battery = robot.battery_pct
            for n in range(10):
                t = base_time - timedelta(minutes=(10 - n) * 5)
                drift = 0.4 if robot.status == "BUSY" else 0.12
                px = round(base_x + rng.uniform(-drift, drift), 3)
                py = round(base_y + rng.uniform(-drift, drift), 3)
                pth = round(base_theta + rng.uniform(-0.1, 0.1), 3)
                bat = max(0, min(100, base_battery - (10 - n if robot.status == "BUSY" else 0)))
                telemetry_rows.append(
                    Telemetry(
                        robot_id=robot.id,
                        x=px,
                        y=py,
                        theta=pth,
                        battery_pct=bat,
                        recorded_at=t,
                        created_at=t,
                    )
                )
        db.add_all(telemetry_rows)

        events: list[Event] = []
        for order in orders:
            events.append(
                Event(
                    event_type="ORDER_CREATED",
                    message=f"Order {order.code} created",
                    order_id=order.id,
                    created_at=order.created_at,
                )
            )
            events.append(
                Event(
                    event_type="ORDER_STATUS_CHANGED",
                    message=f"Order {order.code} status -> {order.status}",
                    order_id=order.id,
                    created_at=order.updated_at,
                )
            )

        for mission in missions:
            events.append(
                Event(
                    event_type="MISSION_CREATED",
                    message=f"Mission {mission.code} created",
                    mission_id=mission.id,
                    order_id=mission.order_id,
                    robot_id=mission.assigned_robot_id,
                    created_at=mission.created_at,
                )
            )
            if mission.assigned_robot_id:
                events.append(
                    Event(
                        event_type="MISSION_ASSIGNED",
                        message=f"Mission {mission.code} assigned",
                        mission_id=mission.id,
                        order_id=mission.order_id,
                        robot_id=mission.assigned_robot_id,
                        created_at=mission.updated_at,
                    )
                )
        db.add_all(events)

        db.commit()
        print(
            "Seed completed: "
            f"{len(robots)} robots, {len(orders)} orders, {len(missions)} missions, "
            f"{len(steps)} steps, {len(telemetry_rows)} telemetry rows, {len(events)} events."
        )
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed fake demo data for Mini WES")
    parser.add_argument(
        "--no-reset",
        action="store_true",
        help="Do not truncate tables before seeding",
    )
    args = parser.parse_args()
    run_seed(reset=not args.no_reset)


if __name__ == "__main__":
    main()
