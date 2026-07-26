"""
AstraX Engine — Difference Imaging
Creates a median reference frame and performs image subtraction for transient detection.
"""

import logging
import numpy as np
from typing import List, Tuple

logger = logging.getLogger("astrax.engine.processing.difference")

def create_median_reference(image_sequence: List[np.ndarray]) -> np.ndarray:
    """
    Creates a median reference frame from a sequence of aligned images.
    """
    if not image_sequence:
        raise ValueError("Empty image sequence provided for reference creation.")
        
    logger.info(f"Creating median reference frame from {len(image_sequence)} images.")
    # Stack along a new axis and take the median
    stacked = np.stack(image_sequence, axis=0)
    reference = np.median(stacked, axis=0)
    return reference

def subtract_images(science_image: np.ndarray, reference_image: np.ndarray) -> np.ndarray:
    """
    Subtracts the reference image from the science image.
    In a full pipeline, we would do PSF matching (e.g., ZOGY or Alard-Lupton) first.
    For this implementation, we assume images are aligned and have similar seeing.
    """
    if science_image.shape != reference_image.shape:
        raise ValueError(f"Shape mismatch: science {science_image.shape} vs ref {reference_image.shape}")
        
    diff = science_image.astype(np.float32) - reference_image.astype(np.float32)
    return diff

def detect_transients(diff_image: np.ndarray, sigma_thresh: float = 5.0) -> List[Tuple[float, float, float]]:
    """
    Detects transients in a difference image.
    Returns a list of (x, y, snr) tuples.
    """
    from astropy.stats import sigma_clipped_stats
    
    mean, median, std = sigma_clipped_stats(diff_image, sigma=3.0)
    
    # Threshold the difference image
    threshold = median + (sigma_thresh * std)
    
    # Find peaks above threshold
    try:
        from photutils.detection import find_peaks
        peaks = find_peaks(diff_image, threshold=threshold, box_size=5)
        
        transients = []
        if peaks is not None:
            for row in peaks:
                x = float(row['x_peak'])
                y = float(row['y_peak'])
                peak_val = float(row['peak_value'])
                snr = (peak_val - median) / (std + 1e-10)
                transients.append((x, y, snr))
                
        return transients
    except ImportError:
        logger.warning("photutils not installed. Skipping peak finding.")
        return []
