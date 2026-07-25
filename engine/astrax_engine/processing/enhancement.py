"""
AstraX Engine — Image Enhancement
CLAHE, contrast stretching, normalization.
"""

import logging
import numpy as np

logger = logging.getLogger("astrax.engine.processing.enhancement")


def clahe_enhance(data: np.ndarray, clip_limit: float = 3.0, tile_size: int = 8) -> np.ndarray:
    """Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)."""
    import cv2

    # Normalize to 0-65535 for 16-bit processing
    vmin, vmax = np.percentile(data, [0.5, 99.5])
    normalized = np.clip((data - vmin) / (vmax - vmin + 1e-10), 0, 1)
    img_16 = (normalized * 65535).astype(np.uint16)

    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(tile_size, tile_size))
    enhanced = clahe.apply(img_16)

    # Map back to original scale
    result = enhanced.astype(np.float64) / 65535.0 * (vmax - vmin) + vmin
    return result


def contrast_stretch(data: np.ndarray, low_pct: float = 1.0, high_pct: float = 99.0) -> np.ndarray:
    """Percentile-based contrast stretching."""
    vmin = np.percentile(data, low_pct)
    vmax = np.percentile(data, high_pct)
    return np.clip((data - vmin) / (vmax - vmin + 1e-10), 0, 1)


def normalize_zscale(data: np.ndarray) -> np.ndarray:
    """ZScale normalization (common in astronomy)."""
    from astropy.visualization import ZScaleInterval
    interval = ZScaleInterval()
    vmin, vmax = interval.get_limits(data)
    return np.clip((data - vmin) / (vmax - vmin + 1e-10), 0, 1)


def normalize_asinh(data: np.ndarray, a: float = 0.1) -> np.ndarray:
    """Asinh stretch — good for high dynamic range astronomical images."""
    from astropy.visualization import AsinhStretch
    stretch = AsinhStretch(a=a)
    # Normalize first
    vmin, vmax = np.percentile(data, [0.5, 99.5])
    normalized = np.clip((data - vmin) / (vmax - vmin + 1e-10), 0, 1)
    return stretch(normalized)


def normalize_minmax(data: np.ndarray) -> np.ndarray:
    """Simple min-max normalization."""
    vmin, vmax = np.min(data), np.max(data)
    if vmax - vmin < 1e-10:
        return np.zeros_like(data)
    return (data - vmin) / (vmax - vmin)
