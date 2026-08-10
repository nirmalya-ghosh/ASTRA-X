"""
AstraX AI — Astrometry API Router
WCS extraction, coordinate conversion, and catalog cross-matching.
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()
logger = logging.getLogger("astrax.api.astrometry")


class WCSRequest(BaseModel):
    dataset_id: int
    frame_index: int = 0


class CatalogMatchRequest(BaseModel):
    dataset_id: int
    frame_index: int = 0
    catalog: str = "I/329"
    radius_arcsec: float = 2.0


@router.post("/solve")
async def solve_wcs(req: WCSRequest):
    """Extract WCS solution from a FITS frame header."""
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

        from pathlib import Path
        frame_path = Path(ds.source_path) / frame.filename

        if not frame_path.exists():
            raise HTTPException(404, "File not found")

        if not frame.filename.lower().endswith(('.fits', '.fit', '.fts')):
            return {"status": "skipped", "reason": "WCS only available for FITS files"}

        from astropy.io import fits
        from astrax_engine.analysis.astrometry import wcs_to_header_dict, pixel_to_world
        from astrax_engine.analysis.photometry import compute_pixel_scale

        with fits.open(str(frame_path)) as hdul:
            header = hdul[0].header
            wcs_dict = wcs_to_header_dict(header)

        if not wcs_dict:
            return {"status": "no_wcs", "message": "No WCS information found in header"}

        pixel_scale = compute_pixel_scale(wcs_dict)

        # Test corners
        shape = (header.get('NAXIS2', 0), header.get('NAXIS1', 0))
        corners = {}
        if shape[0] > 0 and shape[1] > 0:
            for name, (x, y) in [
                ("top_left", (0, 0)),
                ("top_right", (shape[1], 0)),
                ("bottom_left", (0, shape[0])),
                ("bottom_right", (shape[1], shape[0])),
                ("center", (shape[1] / 2, shape[0] / 2)),
            ]:
                ra, dec = pixel_to_world(header, x, y)
                if ra is not None:
                    corners[name] = {"ra": round(ra, 6), "dec": round(dec, 6)}

        return {
            "status": "solved",
            "dataset_id": req.dataset_id,
            "frame_index": req.frame_index,
            "wcs_header": wcs_dict,
            "pixel_scale_arcsec": pixel_scale,
            "image_shape": list(shape),
            "corners": corners,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("WCS solve failed: %s", e)
        raise HTTPException(500, str(e))


@router.post("/catalog")
async def cross_match(req: CatalogMatchRequest):
    """Cross-match detected sources with an astronomical catalog."""
    try:
        from app.db.models import async_session, Candidate
        from sqlalchemy import select

        async with async_session() as session:
            result = await session.execute(
                select(Candidate).where(Candidate.dataset_id == req.dataset_id).limit(100)
            )
            candidates = result.scalars().all()

        if not candidates:
            return {"dataset_id": req.dataset_id, "n_matched": 0, "results": [],
                    "message": "No candidates found. Run detection first."}

        ra_list = [c.ra for c in candidates if c.ra is not None]
        dec_list = [c.dec for c in candidates if c.dec is not None]

        if not ra_list:
            return {"dataset_id": req.dataset_id, "n_matched": 0, "results": [],
                    "message": "No candidates with RA/Dec coordinates."}

        from astrax_engine.analysis.astrometry import cross_match_catalog
        matches = cross_match_catalog(
            ra_list, dec_list,
            catalog=req.catalog,
            radius_arcsec=req.radius_arcsec,
        )

        n_matched = sum(1 for m in matches if m.get("matched"))
        return {
            "dataset_id": req.dataset_id,
            "catalog": req.catalog,
            "n_sources": len(ra_list),
            "n_matched": n_matched,
            "results": matches,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Catalog cross-match failed: %s", e)
        raise HTTPException(500, str(e))
