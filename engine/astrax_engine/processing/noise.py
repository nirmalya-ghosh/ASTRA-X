"""
AstraX Engine — Noise Reduction
Sigma clipping, median filtering, Gaussian filtering, cosmic ray removal.
"""

import logging
import numpy as np

logger = logging.getLogger("astrax.engine.processing.noise")


def sigma_clip_image(data: np.ndarray, sigma: float = 3.0, max_iter: int = 5) -> np.ndarray:
    """Apply sigma clipping to suppress outlier pixels."""
    from astropy.stats import sigma_clip
    clipped = sigma_clip(data, sigma=sigma, maxiters=max_iter, masked=True)
    result = data.copy()
    if np.ma.is_masked(clipped):
        from scipy.ndimage import median_filter
        filtered = median_filter(data, size=5)
        result[clipped.mask] = filtered[clipped.mask]
    return result


def median_filter_image(data: np.ndarray, size: int = 3) -> np.ndarray:
    """Apply median filter for noise reduction."""
    from scipy.ndimage import median_filter
    return median_filter(data, size=size)


def gaussian_filter_image(data: np.ndarray, sigma: float = 1.0) -> np.ndarray:
    """Apply Gaussian filter for smoothing."""
    from scipy.ndimage import gaussian_filter
    return gaussian_filter(data, sigma=sigma)


def remove_cosmic_rays(
    data: np.ndarray,
    gain: float = 1.0,
    readnoise: float = 5.0,
    sigclip: float = 4.5,
    sigfrac: float = 0.3,
    objlim: float = 5.0,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Remove cosmic rays using LACosmic algorithm.
    Returns (cleaned_data, cosmic_ray_mask).
    """
    try:
        import astroscrappy
        cleaned, crmask = astroscrappy.detect_cosmics(
            data.astype(np.float32),
            gain=gain,
            readnoise=readnoise,
            sigclip=sigclip,
            sigfrac=sigfrac,
            objlim=objlim,
        )
        n_removed = np.sum(crmask)
        logger.info(f"Removed {n_removed} cosmic ray pixels")
        return cleaned.astype(np.float64), crmask
    except ImportError:
        logger.warning("astroscrappy not installed, using fallback cosmic ray detection")
        return _fallback_cosmic_ray_removal(data, sigclip)


def ml_cosmic_ray_removal(data: np.ndarray, model_path: str = None) -> tuple[np.ndarray, np.ndarray]:
    """
    Experimental Machine Learning (CNN) based cosmic ray rejection.
    This is a stub for a PyTorch/TensorFlow model that predicts cosmic ray masks.
    """
    logger.info("Initializing ML-based cosmic ray rejection model...")
    # Mocking ML inference
    # In a real scenario, this would load a U-Net or similar CNN to predict the mask
    # e.g., model = torch.load(model_path)
    #       mask = model(torch.tensor(data)).numpy() > 0.5
    
    # For now, we simulate finding cosmic rays using a high threshold
    from astropy.stats import sigma_clipped_stats
    _, _, std = sigma_clipped_stats(data, sigma=3.0)
    
    # Simulate a smart CNN that finds streaks and hot pixels
    mask = data > (np.median(data) + 6 * std)
    
    result = data.copy()
    from scipy.ndimage import median_filter
    filtered = median_filter(data, size=5)
    result[mask] = filtered[mask]
    
    logger.info(f"ML Model identified and removed {np.sum(mask)} cosmic ray pixels")
    return result, mask


def _fallback_cosmic_ray_removal(data: np.ndarray, sigma: float = 4.5) -> tuple[np.ndarray, np.ndarray]:
    """Simple cosmic ray removal using median filter comparison."""
    from scipy.ndimage import median_filter
    from astropy.stats import sigma_clipped_stats

    _, median_bg, std = sigma_clipped_stats(data, sigma=3.0)
    filtered = median_filter(data, size=5)
    diff = data - filtered
    mask = diff > sigma * std

    result = data.copy()
    result[mask] = filtered[mask]
    return result, mask
