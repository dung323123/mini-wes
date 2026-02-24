import csv
import io
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.robot import Robot
from app.models.telemetry import Telemetry
from app.schemas.telemetry import TelemetryIngest, TelemetryLatestItem, TelemetryOut

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


def _now():
    return datetime.now(timezone.utc)


@router.post("/ingest", response_model=TelemetryOut, status_code=201)
def ingest_telemetry(payload: TelemetryIngest, db: Session = Depends(get_db)):
    robot = db.execute(select(Robot).where(Robot.id == payload.robot_id)).scalars().first()
    if not robot:
        raise HTTPException(status_code=404, detail="Robot not found")

    recorded_at = payload.recorded_at or _now()

    row = Telemetry(
        robot_id=payload.robot_id,
        x=payload.x,
        y=payload.y,
        theta=payload.theta,
        battery_pct=payload.battery_pct,
        recorded_at=recorded_at,
        created_at=_now(),
    )
    db.add(row)

    robot.last_pose_x = payload.x
    robot.last_pose_y = payload.y
    robot.last_pose_theta = payload.theta
    robot.battery_pct = payload.battery_pct
    robot.last_seen_at = recorded_at
    robot.updated_at = _now()

    db.commit()
    db.refresh(row)
    return row


@router.get("/latest", response_model=list[TelemetryLatestItem])
def get_latest_telemetry(robot_id: UUID | None = Query(default=None), db: Session = Depends(get_db)):
    if robot_id:
        item = db.execute(
            select(Telemetry).where(Telemetry.robot_id == robot_id).order_by(Telemetry.recorded_at.desc()).limit(1)
        ).scalars().first()
        if not item:
            return []
        return [
            TelemetryLatestItem(
                robot_id=item.robot_id,
                x=item.x,
                y=item.y,
                theta=item.theta,
                battery_pct=item.battery_pct,
                recorded_at=item.recorded_at,
            )
        ]

    robots = db.execute(select(Robot.id)).scalars().all()
    out: list[TelemetryLatestItem] = []
    for rid in robots:
        item = db.execute(
            select(Telemetry).where(Telemetry.robot_id == rid).order_by(Telemetry.recorded_at.desc()).limit(1)
        ).scalars().first()
        if item:
            out.append(
                TelemetryLatestItem(
                    robot_id=item.robot_id,
                    x=item.x,
                    y=item.y,
                    theta=item.theta,
                    battery_pct=item.battery_pct,
                    recorded_at=item.recorded_at,
                )
            )
    return out


@router.get("", response_model=list[TelemetryOut])
def list_telemetry(
    robot_id: UUID | None = Query(default=None),
    from_ts: datetime | None = Query(default=None, alias="from"),
    to_ts: datetime | None = Query(default=None, alias="to"),
    limit: int = Query(default=200, ge=1, le=5000),
    db: Session = Depends(get_db),
):
    stmt = select(Telemetry).order_by(desc(Telemetry.recorded_at)).limit(limit)
    if robot_id:
        stmt = stmt.where(Telemetry.robot_id == robot_id)
    if from_ts:
        stmt = stmt.where(Telemetry.recorded_at >= from_ts)
    if to_ts:
        stmt = stmt.where(Telemetry.recorded_at <= to_ts)
    return db.execute(stmt).scalars().all()


@router.get("/export.csv")
def export_telemetry_csv(
    robot_id: UUID | None = Query(default=None),
    from_ts: datetime | None = Query(default=None, alias="from"),
    to_ts: datetime | None = Query(default=None, alias="to"),
    db: Session = Depends(get_db),
):
    stmt = select(Telemetry).order_by(Telemetry.recorded_at.asc())
    if robot_id:
        stmt = stmt.where(Telemetry.robot_id == robot_id)
    if from_ts:
        stmt = stmt.where(Telemetry.recorded_at >= from_ts)
    if to_ts:
        stmt = stmt.where(Telemetry.recorded_at <= to_ts)

    rows = db.execute(stmt).scalars().all()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "robot_id", "x", "y", "theta", "battery_pct", "recorded_at", "created_at"])
    for row in rows:
        writer.writerow(
            [
                str(row.id),
                str(row.robot_id),
                row.x,
                row.y,
                row.theta,
                row.battery_pct,
                row.recorded_at.isoformat(),
                row.created_at.isoformat(),
            ]
        )
    buf.seek(0)
    filename = f"telemetry-{_now().strftime('%Y%m%d-%H%M%S')}.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
