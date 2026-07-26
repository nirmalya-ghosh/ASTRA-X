"""
AstraX AI — Detection API Router
Handles source detection and motion analysis pipeline.
"""

import logging
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
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
        import asyncio
        async with async_session() as session:
            task = await session.get(ProcessingTask, task_id)
            task.status = "running"
            task.started_at = datetime.utcnow()
            task.message = "Waiting for dataset indexing to complete..."
            await session.commit()
            
            # Wait for the background dataset indexing to complete
            max_wait_seconds = 300  # 5 minutes max wait for large files
            for _ in range(max_wait_seconds):
                dataset = await session.get(Dataset, dataset_id)
                if dataset.status == "ready":
                    break
                elif dataset.status == "error":
                    task.status = "failed"
                    task.error_message = "Dataset indexing failed"
                    await session.commit()
                    return
                await asyncio.sleep(1.0)
                await session.refresh(dataset)

            # Check if we timed out
            await session.refresh(dataset)
            if dataset.status != "ready":
                task.status = "failed"
                task.error_message = f"Dataset indexing timed out (status: {dataset.status})"
                await session.commit()
                return

            task.message = "Loading frames..."
            task.progress = 0.05
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
                task.error_message = "No frames found in dataset. Ensure the dataset finished indexing correctly."
                await session.commit()
                return

            total_frames = len(frames)
            all_candidates = []

            # Sort frames by file extension to determine processing track
            ext = Path(frames[0].file_path).suffix.lower() if frames else ""
            is_image = ext in {".jpg", ".jpeg", ".png", ".tif"}
            is_data = ext in {".csv"}
            is_fits = not (is_image or is_data)

            try:
                from astrax_engine.detection.sources import detect_sources
                from astrax_engine.detection.vision import detect_vision_sources
                from astrax_engine.detection.data import detect_data_anomalies
                has_engine = True
            except ImportError as ie:
                has_engine = False
                logger.warning(f"astrax_engine not installed: {ie}")

            task.message = f"Running {'ensemble ML' if is_data else 'astronomical'} detection on {total_frames} frame(s)..."
            task.progress = 0.1
            await session.commit()

            for i, frame in enumerate(frames):
                progress = 0.1 + (i + 1) / total_frames * 0.7  # 10% to 80%
                task.progress = progress
                task.message = f"Processing {frame.filename} ({i + 1}/{total_frames})..."
                await session.commit()

                if has_engine:
                    sources = []
                    
                    if is_fits:
                        # Astro Pipeline
                        try:
                            sources = detect_sources(frame.file_path, fwhm=fwhm, threshold_sigma=threshold_sigma)
                            task.message = f"DAOStarFinder detected {len(sources)} sources in {frame.filename}"
                            await session.commit()
                        except Exception as e:
                            logger.error(f"FITS detection failed for {frame.filename}: {e}")
                            task.message = f"FITS detection failed for {frame.filename}: {str(e)[:100]}"
                            await session.commit()
                    
                    elif is_image:
                        # Vision Pipeline
                        try:
                            sources = detect_vision_sources(frame.file_path)
                            task.message = f"Vision pipeline detected {len(sources)} objects in {frame.filename}"
                            await session.commit()
                        except Exception as e:
                            logger.error(f"Vision detection failed for {frame.filename}: {e}")
                            task.message = f"Vision detection failed for {frame.filename}: {str(e)[:100]}"
                            await session.commit()
                            
                    elif is_data:
                        # Multi-Model Ensemble Pipeline
                        try:
                            task.message = f"Running 5-model ensemble on {frame.filename} (IsolationForest, LOF, EllipticEnvelope, SGDOneClassSVM, ZScore)..."
                            await session.commit()
                            
                            sources = detect_data_anomalies(frame.file_path)
                            
                            task.message = f"Ensemble detected {len(sources)} anomalies in {frame.filename}"
                            await session.commit()
                        except Exception as e:
                            logger.error(f"Data detection failed for {frame.filename}: {e}", exc_info=True)
                            task.message = f"Data detection failed for {frame.filename}: {str(e)[:100]}"
                            await session.commit()

                    # Map sources to candidates and save to DB
                    for src in sources:
                        # Compute a basic confidence score if not already provided
                        raw_confidence = src.get("confidence_score", 0.0)
                        if raw_confidence == 0.0:
                            # Derive from SNR using sigmoid
                            snr = src.get("snr", 0.0)
                            raw_confidence = 1.0 / (1.0 + np.exp(-0.3 * (snr - 10)))

                        candidate = Candidate(
                            frame_id=frame.id,
                            dataset_id=dataset_id,
                            x_centroid=src.get("x", 0.0),
                            y_centroid=src.get("y", 0.0),
                            flux=src.get("flux"),
                            magnitude=src.get("mag"),
                            snr=src.get("snr"),
                            fwhm=src.get("fwhm"),
                            sharpness=src.get("sharpness"),
                            roundness=src.get("roundness"),
                            confidence_score=round(float(raw_confidence), 4),
                            notes=src.get("notes"),
                            detection_method=src.get("detection_method", "algorithmic"),
                        )
                        session.add(candidate)
                        all_candidates.append(candidate)

                    # Flush after each frame to persist candidates immediately
                    await session.flush()

            # Motion detection (only applicable for FITS sequences)
            if enable_motion and has_engine and len(frames) >= 2 and is_fits:
                task.message = "Analyzing motion across frames..."
                task.progress = 0.85
                await session.commit()

            # False positive filtering
            if enable_filter and has_engine:
                task.message = "Running false positive filter..."
                task.progress = 0.90
                await session.commit()

            # Complete
            task.status = "completed"
            task.progress = 1.0
            task.completed_at = datetime.utcnow()
            task.message = f"Detection complete: {len(all_candidates)} candidates found"
            task.result_json = {
                "total_candidates": len(all_candidates),
                "frames_processed": total_frames,
                "dataset_type": ext,
                "models_used": ["IsolationForest", "LocalOutlierFactor", "EllipticEnvelope", "SGDOneClassSVM", "ZScoreOutlier"] if is_data else ["DAOStarFinder"] if is_fits else ["OpenCV_Vision"],
            }
            await session.commit()

            logger.info(f"Detection task {task_id} completed: {len(all_candidates)} candidates for dataset {dataset_id}")

    except Exception as e:
        logger.error(f"Detection failed for task {task_id}: {e}", exc_info=True)
        try:
            async with async_session() as session:
                task = await session.get(ProcessingTask, task_id)
                if task:
                    task.status = "failed"
                    task.error_message = str(e)
                    await session.commit()
        except Exception:
            pass


# Need numpy for sigmoid calculation
import numpy as np
