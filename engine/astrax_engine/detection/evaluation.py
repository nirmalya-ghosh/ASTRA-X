"""
AstraX Engine — Detection Evaluation
Metrics for measuring asteroid/source detection quality against ground truth.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np


@dataclass
class DetectionMetrics:
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1_score: float
    accuracy: float
    match_radius_px: float


def evaluate_detections(
    detections: Iterable[dict],
    ground_truth: Iterable[dict],
    *,
    match_radius_px: float = 3.0,
) -> DetectionMetrics:
    """
    Compare detected positions to labeled ground-truth positions.

    ``accuracy`` is reported as TP / (TP + FP + FN), which is stricter and more
    useful for sparse object-detection problems than image-wide pixel accuracy.
    """
    detected_points = np.asarray(
        [(float(d["x"]), float(d["y"])) for d in detections],
        dtype=float,
    )
    truth_points = np.asarray(
        [(float(t["x"]), float(t["y"])) for t in ground_truth],
        dtype=float,
    )

    if len(detected_points) == 0 and len(truth_points) == 0:
        return DetectionMetrics(0, 0, 0, 1.0, 1.0, 1.0, 1.0, match_radius_px)
    if len(detected_points) == 0:
        false_negatives = len(truth_points)
        return DetectionMetrics(0, 0, false_negatives, 0.0, 0.0, 0.0, 0.0, match_radius_px)
    if len(truth_points) == 0:
        false_positives = len(detected_points)
        return DetectionMetrics(0, false_positives, 0, 0.0, 0.0, 0.0, 0.0, match_radius_px)

    try:
        from scipy.optimize import linear_sum_assignment

        distances = np.linalg.norm(detected_points[:, None, :] - truth_points[None, :, :], axis=2)
        rows, cols = linear_sum_assignment(distances)
        matches = [(row, col) for row, col in zip(rows, cols) if distances[row, col] <= match_radius_px]
        true_positives = len(matches)
    except ImportError:
        true_positives = _greedy_match_count(detected_points, truth_points, match_radius_px)

    false_positives = len(detected_points) - true_positives
    false_negatives = len(truth_points) - true_positives
    precision = _safe_div(true_positives, true_positives + false_positives)
    recall = _safe_div(true_positives, true_positives + false_negatives)
    f1_score = _safe_div(2 * precision * recall, precision + recall)
    accuracy = _safe_div(true_positives, true_positives + false_positives + false_negatives)

    return DetectionMetrics(
        true_positives=true_positives,
        false_positives=false_positives,
        false_negatives=false_negatives,
        precision=precision,
        recall=recall,
        f1_score=f1_score,
        accuracy=accuracy,
        match_radius_px=match_radius_px,
    )


def meets_accuracy_target(metrics: DetectionMetrics, target: float = 0.99) -> bool:
    """Return whether measured detection accuracy reaches the requested target."""
    return metrics.accuracy >= target


def _safe_div(numerator: float, denominator: float) -> float:
    return float(numerator / denominator) if denominator else 0.0


def _greedy_match_count(detected_points: np.ndarray, truth_points: np.ndarray, radius: float) -> int:
    used_truth = set()
    matches = 0
    for detected in detected_points:
        distances = np.linalg.norm(truth_points - detected, axis=1)
        order = np.argsort(distances)
        for truth_index in order:
            if int(truth_index) not in used_truth and distances[truth_index] <= radius:
                used_truth.add(int(truth_index))
                matches += 1
                break
    return matches
