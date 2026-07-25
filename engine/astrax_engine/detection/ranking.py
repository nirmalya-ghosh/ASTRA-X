"""
AstraX Engine — Candidate Ranking
Multi-factor confidence scoring for moving object candidates.
"""

import logging
import numpy as np

logger = logging.getLogger("astrax.engine.detection.ranking")


def rank_candidates(
    candidates: list[dict],
    weights: dict = None,
) -> list[dict]:
    """
    Rank candidates using a weighted multi-factor score.

    Scoring factors:
    - Motion consistency (linear trajectory fit quality)
    - Brightness stability (flux variation across detections)
    - Shape consistency (roundness stability)
    - Signal-to-noise ratio
    - Detection persistence (fraction of frames detected)
    - Trajectory quality (R² of linear fit)
    - Photometric consistency

    Args:
        candidates: List of candidate dicts
        weights: Optional weight overrides

    Returns:
        Candidates sorted by confidence_score (descending)
    """
    default_weights = {
        "motion_consistency": 0.20,
        "brightness_stability": 0.15,
        "shape_consistency": 0.10,
        "snr": 0.20,
        "persistence": 0.15,
        "trajectory_quality": 0.10,
        "photometric_consistency": 0.10,
    }

    if weights:
        default_weights.update(weights)
    w = default_weights

    for cand in candidates:
        scores = {}

        # SNR score (sigmoid normalization)
        snr = cand.get("snr", 0)
        scores["snr"] = _sigmoid(snr, midpoint=10, steepness=0.3)

        # Motion consistency (requires trajectory data)
        trajectory = cand.get("trajectory", {})
        if trajectory.get("valid"):
            scores["motion_consistency"] = max(0, trajectory.get("r2_avg", 0))
            scores["trajectory_quality"] = max(0, 1.0 - trajectory.get("residual_rms", 1.0) / 5.0)
        else:
            scores["motion_consistency"] = 0.5  # neutral
            scores["trajectory_quality"] = 0.5

        # Persistence score
        detection_count = cand.get("detection_count", 1)
        total_frames = cand.get("total_frames", 1)
        scores["persistence"] = min(1.0, detection_count / max(1, total_frames * 0.5))

        # Shape consistency (roundness close to 0 is star-like)
        roundness = abs(cand.get("roundness", 0))
        scores["shape_consistency"] = max(0, 1.0 - roundness)

        # Brightness stability
        flux_variations = cand.get("flux_variations", [])
        if len(flux_variations) >= 2:
            mean_flux = np.mean(flux_variations)
            std_flux = np.std(flux_variations)
            cv = std_flux / (mean_flux + 1e-10)
            scores["brightness_stability"] = max(0, 1.0 - cv)
        else:
            scores["brightness_stability"] = 0.5

        # Photometric consistency
        scores["photometric_consistency"] = scores["brightness_stability"]

        # Weighted composite score
        confidence = sum(
            scores.get(k, 0.5) * v for k, v in w.items()
        )

        # Risk score (inverse of confidence, weighted by rejection signals)
        risk = 1.0 - confidence
        if cand.get("rejected"):
            risk = min(1.0, risk + 0.3)

        cand["confidence_score"] = round(float(confidence), 4)
        cand["risk_score"] = round(float(risk), 4)
        cand["score_breakdown"] = {k: round(float(v), 4) for k, v in scores.items()}

        # Assign review priority
        if confidence >= 0.8:
            cand["review_priority"] = "high"
        elif confidence >= 0.5:
            cand["review_priority"] = "medium"
        else:
            cand["review_priority"] = "low"

    # Sort by confidence descending
    candidates.sort(key=lambda c: c["confidence_score"], reverse=True)

    logger.info(
        f"Ranked {len(candidates)} candidates: "
        f"{sum(1 for c in candidates if c.get('review_priority') == 'high')} high, "
        f"{sum(1 for c in candidates if c.get('review_priority') == 'medium')} medium, "
        f"{sum(1 for c in candidates if c.get('review_priority') == 'low')} low priority"
    )

    return candidates


def _sigmoid(x: float, midpoint: float = 0, steepness: float = 1.0) -> float:
    """Sigmoid normalization to [0, 1]."""
    return float(1.0 / (1.0 + np.exp(-steepness * (x - midpoint))))
