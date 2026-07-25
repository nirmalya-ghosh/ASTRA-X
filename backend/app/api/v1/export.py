"""
AstraX AI — Export API Router
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import get_session, ProcessingTask
from app.models.schemas import ExportRequest, ExportResponse, TaskStatusResponse

logger = logging.getLogger("astrax.export")
router = APIRouter()


@router.post("", response_model=ExportResponse, status_code=202)
async def create_export(
    body: ExportRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    """Create an export job."""
    task = ProcessingTask(
        task_type="export",
        dataset_id=body.dataset_id,
        status="pending",
        message=f"Export to {body.format} queued",
    )
    session.add(task)
    await session.flush()

    background_tasks.add_task(_run_export, task.id, body)

    return ExportResponse(
        task_id=task.id,
        format=body.format,
        status="pending",
    )


async def _run_export(task_id: int, request: ExportRequest):
    """Background: Run export."""
    from app.db.models import async_session
    from datetime import datetime

    try:
        async with async_session() as session:
            task = await session.get(ProcessingTask, task_id)
            task.status = "running"
            task.started_at = datetime.utcnow()
            await session.commit()

            # TODO: Implement actual export logic
            task.status = "completed"
            task.progress = 1.0
            task.completed_at = datetime.utcnow()
            task.message = "Export complete"
            await session.commit()

    except Exception as e:
        logger.error(f"Export failed: {e}")


@router.get("/{task_id}/status", response_model=TaskStatusResponse)
async def get_export_status(
    task_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get export task status."""
    task = await session.get(ProcessingTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Export task not found")
    return task
