import numpy as np

from astrax_engine.analysis.tracking import ObjectTracker


def test_tracker_links_linear_motion_with_missing_frame():
    tracker = ObjectTracker(max_missing_frames=1, distance_threshold=8.0)

    frames = [
        [{"x": 10.0, "y": 20.0}],
        [{"x": 13.0, "y": 21.5}],
        [],
        [{"x": 19.0, "y": 24.5}],
    ]

    active = []
    for detections in frames:
        active = tracker.update(detections)

    assert len(active) == 1
    track = active[0]
    assert track["id"] == 1
    assert track["length"] == 3
    assert np.hypot(track["dx"], track["dy"]) > 0


def test_tracker_starts_new_track_when_detection_is_too_far():
    tracker = ObjectTracker(distance_threshold=5.0)

    tracker.update([{"x": 0.0, "y": 0.0}])
    active = tracker.update([{"x": 100.0, "y": 100.0}])

    assert len(active) == 2
    assert {track["length"] for track in active} == {1}
