"""Tasks API routes."""

import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.task import Task
from app.models.user import User
from app.schemas.task import QueueStatus, TaskCreate, TaskResponse

router = APIRouter(tags=["tasks"])


def _task_to_response(task: Task) -> TaskResponse:
    return TaskResponse(
        id=task.id,
        user_id=task.user_id,
        status=task.status,
        video_path=task.video_path,
        output_path=task.output_path,
        subtitle_path=task.subtitle_path,
        progress=task.progress,
        stage=task.stage,
        error_message=task.error_message,
        created_at=task.created_at,
        completed_at=task.completed_at,
    )


@router.post("/api/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    body: TaskCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = Task(
        user_id=user.id,
        video_path=body.video_path,
        status="queued",
        config_json=json.dumps({"asr_model": body.asr_model, **body.config}),
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return _task_to_response(task)


@router.get("/api/tasks", response_model=list[TaskResponse])
async def list_tasks(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Task).where(Task.user_id == user.id).order_by(Task.created_at.desc())
    )
    return [_task_to_response(t) for t in result.scalars().all()]


@router.get("/api/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == user.id))
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return _task_to_response(task)


@router.delete("/api/tasks/{task_id}")
async def delete_task(
    task_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == user.id))
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status != "queued":
        raise HTTPException(status_code=409, detail="Can only delete queued tasks")
    await db.delete(task)
    await db.commit()
    return {"detail": "Task deleted"}


@router.get("/api/queue", response_model=QueueStatus)
async def get_queue_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count_result = await db.execute(
        select(sa_func.count()).select_from(Task).where(Task.status == "queued")
    )
    queue_length = count_result.scalar() or 0

    current_result = await db.execute(
        select(Task).where(Task.status == "processing").limit(1)
    )
    current = current_result.scalar_one_or_none()

    return QueueStatus(
        queue_length=queue_length,
        current_task=_task_to_response(current) if current else None,
    )
