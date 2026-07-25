"""
AstraX AI — Tasks API Router
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import get_session, ProcessingTask
from app.models.schemas import TaskStatusResponse

logger = logging.getLogger("astrax.tasks")
router = APIRouter()


@router.get("", response_model=list[TaskStatusResponse])
async def list_tasks(
    task_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    """List processing tasks."""
    query = select(ProcessingTask).order_by(ProcessingTask.created_at.desc())
    if task_type:
        query = query.where(ProcessingTask.task_type == task_type)
    if status:
        query = query.where(ProcessingTask.status == status)

    result = await session.execute(query.limit(limit))
    return result.scalars().all()


@router.get("/{task_id}", response_model=TaskStatusResponse)
async def get_task(
    task_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get task details."""
    from fastapi import HTTPException
    task = await session.get(ProcessingTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
