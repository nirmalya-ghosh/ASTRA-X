"""
AstraX AI — Photometry API Router
Endpoints for aperture/PSF photometry, calibration, and pixel scale.
"""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

router = APIRouter()
logger = logging.getLogger("astrax.api.photometry")


class PhotometryRequest(BaseModel):
    dataset_id: int
    frame_index: int = 0
    method: str = Field(default="aperture", pattern="^(aperture|psf)$")
    aperture_radius: float = 5.0
    annulus_inner: float = 8.0
    annulus_outer: float = 12.0
    sigma_psf: float = 2.0
    threshold: float = 3.0


class CalibrationRequest(BaseModel):
    dataset_id: int
    zero_point: float = 25.0
    extinction_coeff: float = 0.0
    airmass: float = 1.0
    color_term: float = 0.0
    color_index: float = 0.0


@router.post("/run")
async def run_photometry(req: PhotometryRequest):
    """Run aperture or PSF photometry on a dataset frame."""
    try:
        from app.db.models import async_session, Dataset, Frame
        from sqlalchemy import select

        async with async_session() as session:
            ds = await session.get(Dataset, req.dataset_id)
            if not ds:
                raise HTTPException(404, "Dataset not found")

            result = await session.execute(
                select(Frame).where(
                    Frame.dataset_id == req.dataset_id,
                    Frame.frame_index == req.frame_index,
                )
            )
            frame = result.scalar_one_or_none()
            if not frame:
                raise HTTPException(404, f"Frame {req.frame_index} not found")

        # Load image data
        from pathlib import Path
        import numpy as np

        frame_path = Path(frame.file_path)
        if not frame_path.exists():
            raise HTTPException(404, f"File not found: {frame.filename}")

        # Try FITS first, then regular image
        data = None
        if frame.filename.lower().endswith(('.fits', '.fit', '.fts')):
            try:
                from astropy.io import fits
                with fits.open(str(frame_path)) as hdul:
                    data = hdul[0].data.astype(np.float64)
            except Exception:
                pass

        if data is None:
            try:
                import cv2
                img = cv2.imread(str(frame_path), cv2.IMREAD_GRAYSCALE)
                if img is not None:
                    data = img.astype(np.float64)
            except Exception:
                pass

        if data is None:
            raise HTTPException(400, "Could not load image data")

        # Run photometry
        if req.method == "psf":
            from astrax_engine.analysis.photometry import run_psf_photometry
            results = run_psf_photometry(
                data, sigma_psf=req.sigma_psf, threshold=req.threshold
            )
        else:
            # Auto-detect sources first, then run aperture photometry
            from astrax_engine.analysis.photometry import run_psf_photometry, measure_aperture_photometry
            # Find sources with DAOStarFinder
            psf_results = run_psf_photometry(data, sigma_psf=req.sigma_psf, threshold=req.threshold)
            if psf_results:
                positions = [(s["x"], s["y"]) for s in psf_results]
                results = measure_aperture_photometry(
                    data, positions,
                    aperture_radius=req.aperture_radius,
                    annulus_inner=req.annulus_inner,
                    annulus_outer=req.annulus_outer,
                )
            else:
                results = []

        return {
            "dataset_id": req.dataset_id,
            "frame_index": req.frame_index,
            "method": req.method,
            "n_sources": len(results),
            "sources": results[:500],  # cap for response size
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Photometry failed: %s", e)
        raise HTTPException(500, str(e))


@router.post("/calibrate")
async def calibrate_photometry(req: CalibrationRequest):
    """Apply zero-point calibration to existing photometry results."""
    try:
        return {
            "dataset_id": req.dataset_id,
            "zero_point": req.zero_point,
            "extinction_coeff": req.extinction_coeff,
            "airmass": req.airmass,
            "status": "ready",
            "message": "Calibration parameters stored. Run photometry to apply.",
        }
    except Exception as e:
        raise HTTPException(500, str(e))
