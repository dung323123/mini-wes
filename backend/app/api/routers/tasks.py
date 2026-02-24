from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_db
from app.models.mission import Mission
from app.schemas.task import TaskOut, TaskDetailOut

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskOut])
def list_tasks(
    status: str | None = Query(default=None),
    robot_id: UUID | None = Query(default=None),
    order_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
):
    stmt = select(Mission).order_by(Mission.created_at.desc())
    if status:
        stmt = stmt.where(Mission.status == status)
    if robot_id:
        stmt = stmt.where(Mission.assigned_robot_id == robot_id)
    if order_id:
        stmt = stmt.where(Mission.order_id == order_id)
    return db.execute(stmt).scalars().all()


@router.get("/{task_id}", response_model=TaskDetailOut)
def get_task(task_id: UUID, db: Session = Depends(get_db)):
    task = db.execute(
        select(Mission).options(selectinload(Mission.steps)).where(Mission.id == task_id)
    ).scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
