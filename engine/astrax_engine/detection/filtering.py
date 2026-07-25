"""
AstraX Engine — False Positive Filtering
Identifies and suppresses cosmic rays, hot pixels, satellite streaks, etc.
"""

import logging
import numpy as np

logger = logging.getLogger("astrax.engine.detection.filtering")


def filter_false_positives(
    candidates: list[dict],
    data: np.ndarray,
    enable_cosmic_ray: bool = True,
    enable_hot_pixel: bool = True,
    enable_streak: bool = True,
    enable_saturation: bool = True,
    enable_noise: bool = True,
    snr_threshold: float = 3.0,
) -> list[dict]:
    """
    Filter false positive detections from candidate list.

    Args:
        candidates: List of candidate dicts with x, y, flux, etc.
        data: Image data array
        enable_*: Toggle individual filters

    Returns:
        Filtered list of candidates with 'rejected' and 'rejection_reason' fields
    """
    filtered = []

    for cand in candidates:
        x, y = int(round(cand["x"])), int(round(cand["y"]))
        rejected = False
        reason = None

        # Bounds check
        h, w = data.shape
        if x < 2 or x >= w - 2 or y < 2 or y >= h - 2:
            cand["rejected"] = True
            cand["rejection_reason"] = "edge_proximity"
            filtered.append(cand)
            continue

        # Extract local patch
        patch = data[max(0, y-3):y+4, max(0, x-3):x+4]

        if enable_cosmic_ray and not rejected:
            rejected, reason = _check_cosmic_ray(patch, cand)

        if enable_hot_pixel and not rejected:
            rejected, reason = _check_hot_pixel(data, x, y)

        if enable_saturation and not rejected:
            rejected, reason = _check_saturation(patch, data)

        if enable_noise and not rejected:
            if cand.get("snr", float("inf")) < snr_threshold:
                rejected = True
                reason = "low_snr"

        if enable_streak and not rejected:
            rejected, reason = _check_streak(patch)

        cand["rejected"] = rejected
        cand["rejection_reason"] = reason
        filtered.append(cand)

    n_rejected = sum(1 for c in filtered if c.get("rejected"))
    logger.info(f"False positive filter: {n_rejected}/{len(filtered)} rejected")

    return filtered


def _check_cosmic_ray(patch: np.ndarray, candidate: dict) -> tuple[bool, str]:
    """
    Detect cosmic rays by checking sharpness and shape.
    Cosmic rays tend to be very sharp (high contrast in small area)
    and have poor roundness.
    """
    sharpness = candidate.get("sharpness", 0)
    roundness = candidate.get("roundness", 0)

    # Very sharp and not round → likely cosmic ray
    if abs(sharpness) > 0.9 and abs(roundness) > 0.5:
        return True, "cosmic_ray_shape"

    # Check for single-pixel spike
    center = patch[patch.shape[0]//2, patch.shape[1]//2]
    neighbors = np.delete(patch.flatten(), patch.size // 2)
    if len(neighbors) > 0:
        neighbor_std = np.std(neighbors)
        neighbor_mean = np.mean(neighbors)
        if neighbor_std > 0 and (center - neighbor_mean) / neighbor_std > 20:
            return True, "cosmic_ray_spike"

    return False, None


def _check_hot_pixel(data: np.ndarray, x: int, y: int) -> tuple[bool, str]:
    """
    Check for hot/dead pixels.
    Hot pixels are consistently bright across all images.
    Dead pixels are consistently dark.
    """
    # Check if the pixel is extreme compared to local neighborhood
    neighborhood = data[max(0, y-5):y+6, max(0, x-5):x+6]
    if neighborhood.size == 0:
        return False, None

    center_val = data[y, x]
    med = np.median(neighborhood)
    mad = np.median(np.abs(neighborhood - med))

    if mad > 0:
        # Very isolated bright pixel
        zscore = abs(center_val - med) / (1.4826 * mad)
        if zscore > 50:
            return True, "hot_pixel"

    return False, None


def _check_saturation(patch: np.ndarray, full_data: np.ndarray) -> tuple[bool, str]:
    """Check for saturated/overexposed sources."""
    # Estimate saturation level from the full image
    saturation_level = np.percentile(full_data, 99.95)

    if np.max(patch) >= saturation_level:
        # Check how many pixels are saturated
        saturated_fraction = np.sum(patch >= saturation_level) / patch.size
        if saturated_fraction > 0.1:
            return True, "saturated"

    return False, None


def _check_streak(patch: np.ndarray) -> tuple[bool, str]:
    """
    Check for satellite streaks using elongation.
    Streaks are highly elongated compared to point sources.
    """
    # Simple elongation check using moments
    if patch.size < 9:
        return False, None

    try:
        from scipy import ndimage
        threshold = np.median(patch) + 2 * np.std(patch)
        binary = patch > threshold

        if np.sum(binary) < 3:
            return False, None

        # Calculate inertia tensor
        labeled, _ = ndimage.label(binary)
        if labeled.max() == 0:
            return False, None

        # Get the largest region
        largest = labeled == 1
        props = ndimage.find_objects(labeled)
        if not props or props[0] is None:
            return False, None

        slice_y, slice_x = props[0]
        height = slice_y.stop - slice_y.start
        width = slice_x.stop - slice_x.start

        if min(width, height) > 0:
            elongation = max(width, height) / min(width, height)
            if elongation > 5:
                return True, "satellite_streak"
    except Exception:
        pass

    return False, None


def remove_duplicates(
    candidates: list[dict],
    distance_threshold: float = 3.0,
) -> list[dict]:
    """
    Remove duplicate detections that are within distance_threshold pixels.
    Uses Scikit-Learn DBSCAN for robust spatial clustering.
    Keeps the candidate with highest flux in each cluster.
    """
    if not candidates or len(candidates) < 2:
        return candidates

    try:
        from sklearn.cluster import DBSCAN
        
        # Extract coordinates for clustering
        coords = np.array([[c["x"], c["y"]] for c in candidates])
        
        # DBSCAN clustering
        # eps is the max distance between two samples for one to be considered as in the neighborhood of the other
        clustering = DBSCAN(eps=distance_threshold, min_samples=1).fit(coords)
        labels = clustering.labels_
        
        kept = []
        for cluster_id in set(labels):
            if cluster_id == -1: # Noise points (shouldn't happen with min_samples=1)
                continue
                
            # Get all candidates in this cluster
            cluster_cands = [candidates[i] for i in range(len(labels)) if labels[i] == cluster_id]
            
            # Keep the one with the highest flux
            best_cand = max(cluster_cands, key=lambda c: c.get("flux", 0))
            kept.append(best_cand)
            
        n_removed = len(candidates) - len(kept)
        if n_removed > 0:
            logger.info(f"DBSCAN removed {n_removed} duplicate spatial detections")
            
        return kept
        
    except ImportError:
        logger.warning("scikit-learn not installed, falling back to basic duplicate removal")
        # Fallback to basic method if sklearn is missing
        sorted_cands = sorted(candidates, key=lambda c: c.get("flux", 0), reverse=True)
        kept = []
        for cand in sorted_cands:
            is_duplicate = False
            for existing in kept:
                dx = cand["x"] - existing["x"]
                dy = cand["y"] - existing["y"]
                dist = np.sqrt(dx**2 + dy**2)
                if dist < distance_threshold:
                    is_duplicate = True
                    break
            if not is_duplicate:
                kept.append(cand)
        return kept
