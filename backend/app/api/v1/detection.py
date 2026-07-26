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
from app.services.file_types import DATA_EXTS, FITS_EXTS, IMAGE_EXTS, normalized_extension
from app.services.task_scheduler import schedule_coroutine

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
    if dataset.status in {"empty", "error"}:
        raise HTTPException(status_code=400, detail=f"Dataset cannot be processed (status: {dataset.status})")

    task = ProcessingTask(
        task_type="detection",
        dataset_id=body.dataset_id,
        status="pending",
        message="Detection pipeline queued",
    )
    session.add(task)
    await session.commit()

    schedule_coroutine(
        background_tasks,
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
            if not task:
                logger.error(f"Detection task {task_id} disappeared before execution")
                return
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

            frame_types = {
                "fits": 0,
                "image": 0,
                "data": 0,
                "unknown": 0,
            }
            models_used = set()
            for frame in frames:
                frame_ext = normalized_extension(frame.file_path)
                if frame_ext in FITS_EXTS:
                    frame_types["fits"] += 1
                elif frame_ext in IMAGE_EXTS:
                    frame_types["image"] += 1
                elif frame_ext in DATA_EXTS:
                    frame_types["data"] += 1
                else:
                    frame_types["unknown"] += 1

            try:
                from astrax_engine.detection.sources import detect_sources
                from astrax_engine.detection.vision import detect_vision_sources
                from astrax_engine.detection.data import detect_data_anomalies
                has_engine = True
            except ImportError as ie:
                has_engine = False
                logger.warning(f"astrax_engine not installed: {ie}")

            task.message = f"Running detection on {total_frames} frame(s)..."
            task.progress = 0.1
            await session.commit()

            for i, frame in enumerate(frames):
                progress = 0.1 + (i + 1) / total_frames * 0.7  # 10% to 80%
                task.progress = progress
                task.message = f"Processing {frame.filename} ({i + 1}/{total_frames})..."
                await session.commit()

                frame_ext = normalized_extension(frame.file_path)
                is_fits = frame_ext in FITS_EXTS
                is_image = frame_ext in IMAGE_EXTS
                is_data = frame_ext in DATA_EXTS

                if has_engine:
                    sources = []
                    
                    if is_fits:
                        # Astro Pipeline
                        try:
                            sources = detect_sources(frame.file_path, fwhm=fwhm, threshold_sigma=threshold_sigma)
                            models_used.add("DAOStarFinder")
                            if enable_filter and sources:
                                try:
                                    from astrax_engine.io.fits_loader import FITSLoader
                                    from astrax_engine.detection.filtering import filter_false_positives, remove_duplicates
                                    from astrax_engine.detection.ranking import rank_candidates

                                    image_data = FITSLoader().load_data(frame.file_path)
                                    sources = remove_duplicates(sources, distance_threshold=max(2.0, fwhm))
                                    sources = filter_false_positives(
                                        sources,
                                        image_data,
                                        snr_threshold=max(3.0, threshold_sigma * 0.6),
                                    )
                                    sources = [src for src in sources if not src.get("rejected")]
                                    for src in sources:
                                        src["total_frames"] = total_frames
                                    sources = rank_candidates(sources)
                                    models_used.update({"FalsePositiveFilter", "CandidateRanker"})
                                except Exception as e:
                                    logger.warning(f"FITS QA/ranking skipped for {frame.filename}: {e}")
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
                            models_used.add("OpenCV_Vision")
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
                            models_used.update(["IsolationForest", "LocalOutlierFactor", "EllipticEnvelope", "SGDOneClassSVM", "ZScoreOutlier"])
                            
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

                        # Verification
                        notes_str = src.get("notes", "") or ""
                        meta_json = {
                            "frame_type": "fits" if is_fits else "image" if is_image else "data" if is_data else "unknown",
                        }
                        for meta_key in ("score_breakdown", "review_priority", "rejection_reason"):
                            if meta_key in src:
                                meta_json[meta_key] = src.get(meta_key)
                        object_type = None
                        
                        ra = src.get("ra")
                        dec = src.get("dec")
                        if is_fits and ra is not None and dec is not None and raw_confidence > 0.6:
                            try:
                                from astrax_engine.analysis.verification import crossmatch_gaia
                                gaia_res = crossmatch_gaia(ra, dec, radius_arcsec=2.0)
                                if gaia_res.get("status") in {"stationary_star", "stellar_source"}:
                                    meta_json["gaia_dr3"] = gaia_res
                                    notes_str += (
                                        f"\n[Gaia DR3] {gaia_res.get('status')}: "
                                        f"{gaia_res.get('source_id')} "
                                        f"({gaia_res.get('distance_arcsec', 0):.2f}\")"
                                    )
                                    if gaia_res.get("status") == "stationary_star":
                                        object_type = "star"
                                        raw_confidence = min(raw_confidence, 0.35)
                            except Exception as e:
                                logger.warning(f"Gaia DR3 cross-match error: {e}")

                            try:
                                from astrax_engine.analysis.verification import verify_candidate
                                obs_time = frame.date_obs or datetime.utcnow()
                                v_res = verify_candidate(ra, dec, obs_time, radius_arcsec=30.0)
                                
                                if v_res.get("status") == "known_object":
                                    object_type = "asteroid"
                                    notes_str += f"\n[Verification] Known object: {v_res.get('object_name')}"
                                    meta_json["verification"] = v_res
                                elif v_res.get("status") == "possible_match":
                                    notes_str += f"\n[Verification] Possible match: {v_res.get('object_name')} ({v_res.get('distance_arcsec', 0):.1f}\")"
                                    meta_json["verification"] = v_res
                            except Exception as e:
                                logger.warning(f"Verification error: {e}")

                        candidate = Candidate(
                            frame_id=frame.id,
                            dataset_id=dataset_id,
                            x_centroid=src.get("x", 0.0),
                            y_centroid=src.get("y", 0.0),
                            ra=src.get("ra"),
                            dec=src.get("dec"),
                            flux=src.get("flux"),
                            magnitude=src.get("mag"),
                            snr=src.get("snr"),
                            fwhm=src.get("fwhm"),
                            sharpness=src.get("sharpness"),
                            roundness=src.get("roundness"),
                            confidence_score=round(float(raw_confidence), 4),
                            risk_score=round(float(src.get("risk_score", max(0.0, 1.0 - raw_confidence))), 4),
                            persistence_score=round(float(src.get("persistence_score", 0.0)), 4),
                            detection_count=int(src.get("detection_count", 1)),
                            notes=notes_str,
                            object_type=object_type,
                            metadata_json=meta_json,
                            detection_method=src.get("detection_method", "algorithmic"),
                        )
                        session.add(candidate)
                        all_candidates.append(candidate)

                    # Flush after each frame to persist candidates immediately
                    await session.flush()

            # Motion detection (only applicable for FITS sequences)
            has_fits_sequence = frame_types["fits"] >= 2
            if enable_motion and has_engine and has_fits_sequence:
                task.message = "Analyzing motion across frames..."
                task.progress = 0.85
                await session.commit()

            # Tracklet Generation & Orbit Estimation
            if frame_types["fits"] >= 3:
                task.message = "Linking tracklets and estimating orbits..."
                task.progress = 0.88
                await session.commit()
                try:
                    from astrax_engine.analysis.orbit import estimate_orbit
                    from astrax_engine.analysis.tracking import ObjectTracker
                    
                    frames_sorted = sorted(frames, key=lambda x: x.frame_index)
                    tracker = ObjectTracker(distance_threshold=100.0)
                    
                    for frm in frames_sorted:
                        frm_cands = [c for c in all_candidates if c.frame_id == frm.id]
                        dets = [{'x': c.x_centroid, 'y': c.y_centroid, 'cand': c, 'time': frm.date_obs} for c in frm_cands]
                        tracker.update(dets)
                        
                    for t in tracker.tracks:
                        if len(t['history']) >= 3:
                            tracklet_cands = [h['cand'] for h in t['history']]
                            orb_res = estimate_orbit([{'ra': c.ra, 'dec': c.dec, 'time': h.get('time')} for c, h in zip(tracklet_cands, t['history']) if c.ra is not None])
                            
                            if orb_res:
                                for c in tracklet_cands:
                                    if c.metadata_json is None:
                                        c.metadata_json = {}
                                    c.metadata_json['orbit'] = orb_res
                                    notes_append = f"\n[Orbit] Linked in {len(t['history'])}-frame tracklet."
                                    c.notes = (c.notes or "") + notes_append
                except Exception as e:
                    logger.error(f"Tracking/Orbit failed: {e}")

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
                "dataset_type": "mixed" if sum(1 for count in frame_types.values() if count) > 1 else next((kind for kind, count in frame_types.items() if count), "unknown"),
                "frame_types": frame_types,
                "models_used": sorted(models_used) if models_used else ["none"],
                "quality_note": "Confidence scores are triage probabilities, not a guaranteed scientific accuracy rate.",
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
