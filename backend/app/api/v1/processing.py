"""
AstraX AI — Processing API Router
Handles image processing pipeline execution.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import get_session, Dataset, ProcessingTask
from app.models.schemas import ProcessingRequest, TaskStatusResponse

logger = logging.getLogger("astrax.processing")
router = APIRouter()


@router.post("/run", response_model=TaskStatusResponse, status_code=202)
async def run_processing(
    body: ProcessingRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    """Launch the image processing pipeline on a dataset."""
    dataset = await session.get(Dataset, body.dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if dataset.status != "ready":
        raise HTTPException(status_code=400, detail=f"Dataset not ready (status: {dataset.status})")

    task = ProcessingTask(
        task_type="processing",
        dataset_id=body.dataset_id,
        status="pending",
        message="Processing pipeline queued",
    )
    session.add(task)
    await session.flush()

    # TODO: Launch processing pipeline in background
    background_tasks.add_task(_run_processing_pipeline, task.id, body.dataset_id, body.steps)

    return task


async def _run_processing_pipeline(task_id: int, dataset_id: int, steps: list):
    """Background: Run the processing pipeline."""
    from app.db.models import async_session
    from datetime import datetime

    try:
        async with async_session() as session:
            task = await session.get(ProcessingTask, task_id)
            if not task:
                return
            task.status = "running"
            task.started_at = datetime.utcnow()
            task.message = "Processing started"
            await session.commit()

        # TODO: Execute actual processing steps via engine
        # For now, mark as completed
        async with async_session() as session:
            task = await session.get(ProcessingTask, task_id)
            task.status = "completed"
            task.progress = 1.0
            task.completed_at = datetime.utcnow()
            task.message = "Processing completed"
            await session.commit()

    except Exception as e:
        logger.error(f"Processing failed for task {task_id}: {e}")
        async with async_session() as session:
            task = await session.get(ProcessingTask, task_id)
            if task:
                task.status = "failed"
                task.error_message = str(e)
                await session.commit()


@router.get("/{task_id}/status", response_model=TaskStatusResponse)
async def get_processing_status(
    task_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get the status of a processing task."""
    task = await session.get(ProcessingTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
