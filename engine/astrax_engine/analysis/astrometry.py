"""
AstraX Engine — Astrometry
WCS coordinate transformations and blind plate-solving helpers.
"""

from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Any, Iterable, Optional, Tuple

logger = logging.getLogger("astrax.engine.analysis.astrometry")


@dataclass
class BlindSolveConfig:
    """Configuration for blind plate solving via Astrometry.net."""

    api_key: Optional[str] = None
    scale_units: str = "arcsecperpix"
    scale_lower: Optional[float] = None
    scale_upper: Optional[float] = None
    center_ra: Optional[float] = None
    center_dec: Optional[float] = None
    radius: Optional[float] = None
    solve_timeout: int = 120


def _to_wcs(wcs_like: Any):
    """Build an Astropy WCS from an existing WCS, FITS header, or plain dict."""
    from astropy.io import fits
    from astropy.wcs import WCS

    if isinstance(wcs_like, WCS):
        return wcs_like
    if isinstance(wcs_like, fits.Header):
        return WCS(wcs_like)
    if not isinstance(wcs_like, dict):
        raise TypeError(f"Unsupported WCS input: {type(wcs_like)!r}")

    header = fits.Header()
    for key, value in wcs_like.items():
        if isinstance(key, str) and len(key) <= 8:
            try:
                header[key] = value
            except ValueError:
                pass
    return WCS(header)


def wcs_to_header_dict(wcs_like: Any) -> dict:
    """Serialize a WCS-like object to a JSON-friendly FITS header dictionary."""
    try:
        wcs = _to_wcs(wcs_like)
        return {
            key: value
            for key, value in wcs.to_header(relax=True).items()
            if isinstance(value, (str, int, float, bool))
        }
    except Exception as exc:
        logger.warning(f"WCS serialization failed: {exc}")
        return {}


def pixel_to_world(wcs_header: Any, x: float, y: float) -> Tuple[Optional[float], Optional[float]]:
    """Convert pixel coordinates to RA/Dec."""
    try:
        w = _to_wcs(wcs_header)
        if not w.is_celestial:
            return (None, None)

        ra, dec = w.all_pix2world(x, y, 0)
        return float(ra), float(dec)

    except Exception as e:
        logger.warning(f"WCS conversion failed: {e}")
        return (None, None)


def world_to_pixel(wcs_header: Any, ra: float, dec: float) -> Tuple[Optional[float], Optional[float]]:
    """Convert RA/Dec to pixel coordinates."""
    try:
        w = _to_wcs(wcs_header)
        if not w.is_celestial:
            return (None, None)

        x, y = w.all_world2pix(ra, dec, 0)
        return float(x), float(y)

    except Exception as e:
        logger.warning(f"WCS conversion failed: {e}")
        return (None, None)


def solve_blind(
    image_path: str | Path,
    config: Optional[BlindSolveConfig] = None,
    *,
    api_key: Optional[str] = None,
) -> dict:
    """
    Blind-solve an astronomical image with Astrometry.net.

    This keeps the production dependency light: when ``astroquery`` or an API key
    is unavailable, the caller receives an explicit skipped/failed status instead
    of an exception. ``api_key`` can also be provided through ``ASTRAX_ASTROMETRY_NET_API_KEY``.
    """
    import os

    cfg = config or BlindSolveConfig()
    cfg.api_key = api_key or cfg.api_key or os.getenv("ASTRAX_ASTROMETRY_NET_API_KEY")
    if not cfg.api_key:
        return {
            "status": "skipped",
            "reason": "Astrometry.net API key not configured",
            "solver": "astrometry.net",
        }

    try:
        from astroquery.astrometry_net import AstrometryNet

        solver = AstrometryNet()
        solver.api_key = cfg.api_key

        solve_kwargs = {
            "solve_timeout": cfg.solve_timeout,
            "scale_units": cfg.scale_units,
        }
        for key in ("scale_lower", "scale_upper", "center_ra", "center_dec", "radius"):
            value = getattr(cfg, key)
            if value is not None:
                solve_kwargs[key] = value

        header = solver.solve_from_image(str(image_path), **solve_kwargs)
        if not header:
            return {
                "status": "failed",
                "reason": "Astrometry.net returned no WCS solution",
                "solver": "astrometry.net",
            }

        return {
            "status": "solved",
            "solver": "astrometry.net",
            "wcs_header": wcs_to_header_dict(header),
        }
    except ImportError:
        return {
            "status": "skipped",
            "reason": "astroquery is not installed",
            "solver": "astrometry.net",
        }
    except Exception as exc:
        logger.error(f"Blind plate solving failed for {image_path}: {exc}")
        return {
            "status": "failed",
            "reason": str(exc),
            "solver": "astrometry.net",
        }


def fit_wcs_from_points(
    pixel_points: Iterable[tuple[float, float]],
    sky_points: Iterable[tuple[float, float]],
    image_shape: Optional[tuple[int, int]] = None,
) -> dict:
    """
    Fit a linear TAN WCS from matched pixel and sky points.

    This is not blind solving by itself, but it gives tests and offline workflows a
    deterministic way to validate downstream WCS plumbing after catalog matching.
    """
    try:
        import numpy as np
        from astropy.coordinates import SkyCoord
        from astropy.wcs.utils import fit_wcs_from_points as astropy_fit_wcs

        pixels = np.asarray(list(pixel_points), dtype=float)
        sky = np.asarray(list(sky_points), dtype=float)
        if len(pixels) < 3 or len(sky) < 3 or len(pixels) != len(sky):
            raise ValueError("At least three matched pixel/sky points are required")

        coords = SkyCoord(sky[:, 0], sky[:, 1], unit="deg", frame="icrs")
        wcs = astropy_fit_wcs((pixels[:, 0], pixels[:, 1]), coords, projection="TAN")
        if image_shape:
            wcs.array_shape = image_shape
        return {
            "status": "solved",
            "solver": "linear-fit",
            "wcs_header": wcs_to_header_dict(wcs),
        }
    except Exception as exc:
        logger.warning(f"Matched-point WCS fit failed: {exc}")
        return {"status": "failed", "reason": str(exc), "solver": "linear-fit"}


def cross_match_catalog(
    ra_list: list[float],
    dec_list: list[float],
    catalog: str = "I/329",
    radius_arcsec: float = 2.0,
    fields: Optional[list[str]] = None,
) -> list[dict]:
    """
    Cross-match source positions with a Vizier catalog.
    Inspired by astrokit's catalog.py URAT1 lookup.

    Parameters
    ----------
    ra_list : source RA in degrees
    dec_list : source Dec in degrees
    catalog : Vizier catalog ID (default URAT1 = I/329)
    radius_arcsec : matching radius in arcseconds
    fields : specific catalog fields to retrieve

    Returns
    -------
    list of matched source dicts
    """
    if fields is None:
        fields = ['_RAJ2000', '_DEJ2000', 'Bmag', 'Vmag', 'gmag', 'rmag', 'imag']

    try:
        from astroquery.vizier import Vizier
        import astropy.units as u

        vizier = Vizier(columns=fields)
        vizier.ROW_LIMIT = 1

        results = []
        for ra, dec in zip(ra_list, dec_list):
            search_str = f"{ra} {dec}"
            try:
                matches = vizier.query_region(
                    search_str, radius=f"{radius_arcsec}s", catalog=catalog
                )
                if matches and len(matches) > 0 and len(matches[0]) > 0:
                    row = matches[0][0]
                    entry = {"ra": ra, "dec": dec, "matched": True}
                    for f in fields:
                        try:
                            val = row[f]
                            entry[f] = float(val) if val is not None else None
                        except (KeyError, ValueError, TypeError):
                            entry[f] = None
                    results.append(entry)
                else:
                    results.append({"ra": ra, "dec": dec, "matched": False})
            except Exception:
                results.append({"ra": ra, "dec": dec, "matched": False})

        matched_count = sum(1 for r in results if r.get("matched"))
        logger.info("Catalog cross-match: %d/%d sources matched", matched_count, len(ra_list))
        return results

    except ImportError:
        logger.error("astroquery not installed for catalog cross-matching.")
        return [{"ra": ra, "dec": dec, "matched": False} for ra, dec in zip(ra_list, dec_list)]
