"""
AstraX Engine — Source Detection
DAOStarFinder, IRAFStarFinder, and adaptive detection algorithms.
"""

import logging
from typing import Union
from pathlib import Path

import numpy as np

logger = logging.getLogger("astrax.engine.detection")


def detect_sources(
    file_path: Union[str, Path],
    fwhm: float = 3.0,
    threshold_sigma: float = 5.0,
    method: str = "dao",
    data: np.ndarray = None,
) -> list[dict]:
    """
    Detect point sources in a FITS image.

    Args:
        file_path: Path to FITS file (ignored if data is provided)
        fwhm: Expected FWHM of point sources in pixels
        threshold_sigma: Detection threshold in sigma above background
        method: Detection method ('dao', 'iraf', 'adaptive')
        data: Pre-loaded image data (optional)

    Returns:
        List of detected source dictionaries with x, y, flux, etc.
    """
    from astropy.stats import sigma_clipped_stats

    if data is None:
        from astrax_engine.io.fits_loader import FITSLoader
        loader = FITSLoader()
        data = loader.load_data(file_path)

    # Calculate background statistics
    mean, median, std = sigma_clipped_stats(data, sigma=3.0)

    threshold = threshold_sigma * std

    if method == "dao":
        sources = _detect_dao(data - median, fwhm, threshold)
    elif method == "iraf":
        sources = _detect_iraf(data - median, fwhm, threshold)
    elif method == "adaptive":
        sources = _detect_adaptive(data, median, std, fwhm)
    else:
        raise ValueError(f"Unknown detection method: {method}")

    logger.info(f"Detected {len(sources)} sources using {method} (fwhm={fwhm}, σ={threshold_sigma})")
    return sources


def _detect_dao(data: np.ndarray, fwhm: float, threshold: float) -> list[dict]:
    """DAOStarFinder detection."""
    from photutils.detection import DAOStarFinder

    finder = DAOStarFinder(fwhm=fwhm, threshold=threshold)
    table = finder(data)

    if table is None:
        return []

    sources = []
    for row in table:
        sources.append({
            "x": float(row["xcentroid"]),
            "y": float(row["ycentroid"]),
            "flux": float(row["flux"]),
            "mag": float(row["mag"]) if row["mag"] is not None else None,
            "sharpness": float(row["sharpness"]),
            "roundness": float(row["roundness1"]),
            "fwhm": fwhm,
            "peak": float(row["peak"]),
            "id": int(row["id"]),
        })
    return sources


def _detect_iraf(data: np.ndarray, fwhm: float, threshold: float) -> list[dict]:
    """IRAFStarFinder detection."""
    from photutils.detection import IRAFStarFinder

    finder = IRAFStarFinder(fwhm=fwhm, threshold=threshold)
    table = finder(data)

    if table is None:
        return []

    sources = []
    for row in table:
        sources.append({
            "x": float(row["xcentroid"]),
            "y": float(row["ycentroid"]),
            "flux": float(row["flux"]),
            "mag": float(row["mag"]) if row["mag"] is not None else None,
            "sharpness": float(row["sharpness"]),
            "roundness": float(row["roundness"]),
            "fwhm": fwhm,
            "peak": float(row["peak"]),
            "id": int(row["id"]),
        })
    return sources


def _detect_adaptive(
    data: np.ndarray, median: float, std: float, fwhm: float
) -> list[dict]:
    """
    Multi-threshold adaptive detection.
    Runs DAOStarFinder at multiple thresholds and merges results.
    """
    from photutils.detection import DAOStarFinder

    all_sources = {}
    thresholds = [3.0, 5.0, 7.0, 10.0]

    for sigma in thresholds:
        threshold = sigma * std
        finder = DAOStarFinder(fwhm=fwhm, threshold=threshold)
        table = finder(data - median)

        if table is None:
            continue

        for row in table:
            # Use rounded position as key to deduplicate
            key = (round(float(row["xcentroid"]), 1), round(float(row["ycentroid"]), 1))
            if key not in all_sources:
                all_sources[key] = {
                    "x": float(row["xcentroid"]),
                    "y": float(row["ycentroid"]),
                    "flux": float(row["flux"]),
                    "mag": float(row["mag"]) if row["mag"] is not None else None,
                    "sharpness": float(row["sharpness"]),
                    "roundness": float(row["roundness1"]),
                    "fwhm": fwhm,
                    "peak": float(row["peak"]),
                    "snr": float(row["peak"]) / std if std > 0 else 0.0,
                    "detection_sigma": sigma,
                    "id": len(all_sources) + 1,
                }

    return list(all_sources.values())


def detect_with_segmentation(data: np.ndarray, threshold_sigma: float = 2.0) -> list[dict]:
    """
    Detect sources using image segmentation (watershed).
    Better for extended or blended sources.
    """
    from photutils.segmentation import detect_sources as phot_detect, deblend_sources
    from photutils.segmentation import SourceCatalog
    from astropy.stats import sigma_clipped_stats
    from astropy.convolution import Gaussian2DKernel

    mean, median, std = sigma_clipped_stats(data, sigma=3.0)
    threshold = median + threshold_sigma * std

    # Convolve with Gaussian for better detection
    kernel = Gaussian2DKernel(x_stddev=1.5)
    segm = phot_detect(data, threshold, npixels=5, kernel=kernel)

    if segm is None:
        return []

    # Deblend overlapping sources
    try:
        segm_deblended = deblend_sources(data, segm, npixels=5, kernel=kernel)
    except Exception:
        segm_deblended = segm

    cat = SourceCatalog(data, segm_deblended)

    sources = []
    for obj in cat:
        sources.append({
            "x": float(obj.xcentroid),
            "y": float(obj.ycentroid),
            "flux": float(obj.segment_flux),
            "area": int(obj.area.value) if hasattr(obj.area, 'value') else int(obj.area),
            "ellipticity": float(obj.ellipticity.value) if hasattr(obj.ellipticity, 'value') else float(obj.ellipticity),
            "fwhm": float(obj.fwhm.value) if hasattr(obj.fwhm, 'value') else float(obj.fwhm) if obj.fwhm is not None else None,
            "snr": float(obj.segment_flux / (std * np.sqrt(float(obj.area.value if hasattr(obj.area, 'value') else obj.area)))) if std > 0 else 0,
            "id": int(obj.label),
        })

    return sources
