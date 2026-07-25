"""
AstraX Engine — Statistics
Image statistics and SNR calculations.
"""

import logging
import numpy as np
from typing import Dict

logger = logging.getLogger("astrax.engine.analysis.statistics")


def compute_image_statistics(data: np.ndarray, sigma: float = 3.0) -> Dict[str, float]:
    """Compute robust image statistics (sigma-clipped)."""
    try:
        from astropy.stats import sigma_clipped_stats
        mean, median, std = sigma_clipped_stats(data, sigma=sigma)
        
        return {
            "mean": float(mean),
            "median": float(median),
            "std": float(std),
            "min": float(np.min(data)),
            "max": float(np.max(data)),
            "snr_estimate": float(mean / std) if std > 0 else 0.0
        }
    except Exception as e:
        logger.error(f"Failed to compute statistics: {e}")
        # Fallback
        return {
            "mean": float(np.mean(data)),
            "median": float(np.median(data)),
            "std": float(np.std(data)),
            "min": float(np.min(data)),
            "max": float(np.max(data)),
            "snr_estimate": 0.0
        }
