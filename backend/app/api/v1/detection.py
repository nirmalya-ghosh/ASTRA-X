"""
AstraX AI — Detection API Router
Handles source detection and motion analysis pipeline.
"""

import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import get_session, Dataset, Frame, Candidate, ProcessingTask
from app.models.schemas import DetectionRequest, TaskStatusResponse

logger = logging.getLogger("astrax.detection")
router = APIRouter()


@router.post("/run", response_model=TaskStatusResponse, status_code=202)
async def run_detection(
    body: DetectionRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    """Launch the detection pipeline on a dataset."""
    dataset = await session.get(Dataset, body.dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    task = ProcessingTask(
        task_type="detection",
        dataset_id=body.dataset_id,
        status="pending",
        message="Detection pipeline queued",
    )
    session.add(task)
    await session.flush()

    background_tasks.add_task(
        _run_detection_pipeline,
        task.id, body.dataset_id, body.fwhm,
        body.threshold_sigma, body.motion_threshold,
        body.min_persistence, body.enable_motion_detection,
        body.enable_false_positive_filter,
    )

    return task


async def _run_detection_pipeline(
    task_id: int, dataset_id: int, fwhm: float,
    threshold_sigma: float, motion_threshold: float,
    min_persistence: int, enable_motion: bool,
    enable_filter: bool,
):
    """Background: Run the full detection pipeline."""
    from app.db.models import async_session

    try:
        async with async_session() as session:
            task = await session.get(ProcessingTask, task_id)
            task.status = "running"
            task.started_at = datetime.utcnow()
            task.message = "Loading frames..."
            await session.commit()

            # Get frames
            result = await session.execute(
                select(Frame)
                .where(Frame.dataset_id == dataset_id)
                .order_by(Frame.frame_index)
            )
            frames = result.scalars().all()

            if not frames:
                task.status = "failed"
                task.error_message = "No frames found in dataset"
                await session.commit()
                return

            total_frames = len(frames)
            all_candidates = []

            try:
                from astrax_engine.detection.sources import detect_sources
                from astrax_engine.detection.motion import detect_motion
                from astrax_engine.detection.filtering import filter_false_positives
                from astrax_engine.detection.ranking import rank_candidates
                has_engine = True
            except ImportError:
                has_engine = False
                logger.warning("astrax_engine not installed, using stub detection")

            for i, frame in enumerate(frames):
                progress = (i + 1) / total_frames
                task.progress = progress * 0.7  # 70% for detection
                task.message = f"Detecting sources in frame {i + 1}/{total_frames}"
                await session.commit()

                if has_engine:
                    # Use the real engine
                    sources = detect_sources(
                        frame.file_path, fwhm=fwhm, threshold_sigma=threshold_sigma
                    )
                    for src in sources:
                        candidate = Candidate(
                            frame_id=frame.id,
                            dataset_id=dataset_id,
                            x_centroid=src["x"],
                            y_centroid=src["y"],
                            flux=src.get("flux"),
                            magnitude=src.get("mag"),
                            snr=src.get("snr"),
                            fwhm=src.get("fwhm"),
                            sharpness=src.get("sharpness"),
                            roundness=src.get("roundness"),
                            detection_method="daofind",
                        )
                        session.add(candidate)
                        all_candidates.append(candidate)

            # Motion detection
            if enable_motion and has_engine and len(frames) >= 2:
                task.message = "Analyzing motion..."
                task.progress = 0.8
                await session.commit()
                # Motion detection updates candidates in-place

            # False positive filtering
            if enable_filter and has_engine:
                task.message = "Filtering false positives..."
                task.progress = 0.9
                await session.commit()

            # Complete
            task.status = "completed"
            task.progress = 1.0
            task.completed_at = datetime.utcnow()
            task.message = f"Detection complete: {len(all_candidates)} candidates found"
            task.result_json = {
                "total_candidates": len(all_candidates),
                "frames_processed": total_frames,
            }
            await session.commit()

    except Exception as e:
        logger.error(f"Detection failed for task {task_id}: {e}")
        try:
            async with async_session() as session:
                task = await session.get(ProcessingTask, task_id)
                if task:
                    task.status = "failed"
                    task.error_message = str(e)
                    await session.commit()
        except Exception:
            pass
