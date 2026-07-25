"""
AstraX Engine — Image Calibration
Flat field, dark frame, bias correction, and bad pixel masking.
"""

import logging
import numpy as np
from typing import Optional

logger = logging.getLogger("astrax.engine.processing.calibration")


def apply_flat_field(data: np.ndarray, flat: np.ndarray) -> np.ndarray:
    """Apply flat field correction. Divides data by normalized flat."""
    flat_norm = flat / np.median(flat)
    flat_norm[flat_norm < 0.01] = 1.0  # Avoid division by zero
    return data / flat_norm


def subtract_dark(data: np.ndarray, dark: np.ndarray, scale: float = 1.0) -> np.ndarray:
    """Subtract dark frame, optionally scaled by exposure ratio."""
    return data - dark * scale


def subtract_bias(data: np.ndarray, bias: np.ndarray) -> np.ndarray:
    """Subtract bias frame."""
    return data - bias


def apply_bad_pixel_mask(
    data: np.ndarray,
    mask: np.ndarray = None,
    hot_threshold: float = 50.0,
    dead_threshold: float = -10.0,
) -> np.ndarray:
    """Replace bad pixels with local median."""
    from scipy.ndimage import median_filter

    if mask is None:
        # Auto-detect bad pixels
        from astropy.stats import sigma_clipped_stats
        _, median, std = sigma_clipped_stats(data, sigma=3.0)
        mask = (data > median + hot_threshold * std) | (data < median + dead_threshold * std)

    if np.any(mask):
        filtered = median_filter(data, size=5)
        result = data.copy()
        result[mask] = filtered[mask]
        logger.info(f"Masked {np.sum(mask)} bad pixels")
        return result

    return data


def full_calibration(
    data: np.ndarray,
    flat: Optional[np.ndarray] = None,
    dark: Optional[np.ndarray] = None,
    bias: Optional[np.ndarray] = None,
    exposure_ratio: float = 1.0,
) -> np.ndarray:
    """Apply full calibration chain: bias → dark → flat."""
    result = data.astype(np.float64)

    if bias is not None:
        result = subtract_bias(result, bias)
        logger.info("Applied bias correction")

    if dark is not None:
        result = subtract_dark(result, dark, scale=exposure_ratio)
        logger.info("Applied dark subtraction")

    if flat is not None:
        result = apply_flat_field(result, flat)
        logger.info("Applied flat field correction")

    return result
