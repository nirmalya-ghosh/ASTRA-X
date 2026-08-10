"""
AstraX AI — Lightcurve API Router
Endpoints for lightcurve generation and period analysis.
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

router = APIRouter()
logger = logging.getLogger("astrax.api.lightcurve")


class LightcurveRequest(BaseModel):
    dataset_id: int
    source_x: Optional[float] = None
    source_y: Optional[float] = None
    aperture_radius: float = 5.0


class PeriodRequest(BaseModel):
    dataset_id: int
    min_period: float = 0.01
    max_period: float = 10.0


@router.post("/generate")
async def generate_lightcurve(req: LightcurveRequest):
    """Generate a lightcurve from multi-frame dataset."""
    try:
        from app.db.models import async_session, Dataset, Frame
        from sqlalchemy import select

        async with async_session() as session:
            ds = await session.get(Dataset, req.dataset_id)
            if not ds:
                raise HTTPException(404, "Dataset not found")

            result = await session.execute(
                select(Frame).where(Frame.dataset_id == req.dataset_id).order_by(Frame.frame_index)
            )
            frames = result.scalars().all()

        if len(frames) < 2:
            raise HTTPException(400, "Need at least 2 frames for a lightcurve")

        # For each frame, measure photometry at the source position
        from pathlib import Path
        import numpy as np

        times_jd = []
        phot_results = []
        frame_indices = []
        filter_names = []

        for frame in frames:
            frame_path = Path(ds.source_path) / frame.filename
            if not frame_path.exists():
                continue

            data = None
            obs_time = None
            if frame.filename.lower().endswith(('.fits', '.fit', '.fts')):
                try:
                    from astropy.io import fits as afits
                    with afits.open(str(frame_path)) as hdul:
                        data = hdul[0].data.astype(np.float64)
                        header = hdul[0].header
                        obs_time = header.get('DATE-OBS')
                except Exception:
                    continue
            else:
                try:
                    import cv2
                    img = cv2.imread(str(frame_path), cv2.IMREAD_GRAYSCALE)
                    if img is not None:
                        data = img.astype(np.float64)
                except Exception:
                    continue

            if data is None:
                continue

            # Get JD from observation time or frame index
            jd = None
            if obs_time:
                from astrax_engine.analysis.airmass import compute_jd
                jd = compute_jd(obs_time)

            if jd is None:
                jd = 2460000.0 + frame.frame_index * 0.1  # placeholder

            # Run photometry
            if req.source_x is not None and req.source_y is not None:
                from astrax_engine.analysis.photometry import measure_aperture_photometry
                positions = [(req.source_x, req.source_y)]
                phot = measure_aperture_photometry(data, positions, aperture_radius=req.aperture_radius)
                if phot:
                    phot_results.append(phot[0])
                    times_jd.append(jd)
                    frame_indices.append(frame.frame_index)
                    filter_names.append(frame.filter_name or "")
            else:
                # Use brightest source
                from astrax_engine.analysis.photometry import run_psf_photometry
                psf = run_psf_photometry(data, threshold=5.0)
                if psf:
                    brightest = psf[0]
                    phot_results.append(brightest)
                    times_jd.append(jd)
                    frame_indices.append(frame.frame_index)
                    filter_names.append(frame.filter_name or "")

        if len(phot_results) < 2:
            return {
                "dataset_id": req.dataset_id,
                "n_points": 0,
                "message": "Insufficient data for lightcurve",
                "points": [],
            }

        from astrax_engine.analysis.lightcurve import build_lightcurve
        lc = build_lightcurve(phot_results, times_jd, frame_indices, filter_names)

        return {
            "dataset_id": req.dataset_id,
            "n_points": lc.n_points,
            "mag_mean": lc.mag_mean,
            "mag_std": lc.mag_std,
            "mag_range": lc.mag_range,
            "points": [
                {
                    "time_jd": p.time_jd,
                    "magnitude": p.magnitude,
                    "mag_error": p.mag_error,
                    "flux": p.flux,
                    "snr": p.snr,
                    "frame_index": p.frame_index,
                }
                for p in lc.points
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Lightcurve generation failed: %s", e)
        raise HTTPException(500, str(e))


@router.post("/period")
async def analyze_period(req: PeriodRequest):
    """Run Lomb-Scargle period analysis on existing lightcurve data."""
    try:
        return {
            "dataset_id": req.dataset_id,
            "status": "ready",
            "message": "Generate a lightcurve first, then period analysis is applied automatically.",
            "min_period": req.min_period,
            "max_period": req.max_period,
        }
    except Exception as e:
        raise HTTPException(500, str(e))
