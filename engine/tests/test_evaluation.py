import pytest

from astrax_engine.detection.evaluation import evaluate_detections, meets_accuracy_target


def test_evaluate_detections_reports_perfect_match():
    metrics = evaluate_detections(
        detections=[{"x": 10.1, "y": 10.0}, {"x": 20.0, "y": 20.2}],
        ground_truth=[{"x": 10.0, "y": 10.0}, {"x": 20.0, "y": 20.0}],
        match_radius_px=1.0,
    )

    assert metrics.true_positives == 2
    assert metrics.false_positives == 0
    assert metrics.false_negatives == 0
    assert metrics.accuracy == pytest.approx(1.0)
    assert meets_accuracy_target(metrics, target=0.99)


def test_evaluate_detections_penalizes_false_positive_and_false_negative():
    metrics = evaluate_detections(
        detections=[{"x": 10.0, "y": 10.0}, {"x": 99.0, "y": 99.0}],
        ground_truth=[{"x": 10.0, "y": 10.0}, {"x": 20.0, "y": 20.0}],
        match_radius_px=1.0,
    )

    assert metrics.true_positives == 1
    assert metrics.false_positives == 1
    assert metrics.false_negatives == 1
    assert metrics.precision == pytest.approx(0.5)
    assert metrics.recall == pytest.approx(0.5)
    assert not meets_accuracy_target(metrics, target=0.99)
