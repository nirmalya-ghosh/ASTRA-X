from astrax_engine.analysis.orbit import estimate_orbit


def test_estimate_orbit_requires_three_observations():
    assert estimate_orbit([
        {"ra": 10.0, "dec": 20.0, "time": "2026-01-01T00:00:00"},
        {"ra": 10.1, "dec": 20.1, "time": "2026-01-01T00:10:00"},
    ]) is None


def test_estimate_orbit_marks_short_arc_as_insufficient():
    result = estimate_orbit([
        {"ra": 10.0, "dec": 20.0, "time": "2026-01-01T00:00:00"},
        {"ra": 10.1, "dec": 20.1, "time": "2026-01-01T00:30:00"},
        {"ra": 10.2, "dec": 20.2, "time": "2026-01-01T01:00:00"},
    ])

    assert result is not None
    assert result["status"] == "insufficient_arc"
    assert result["observations_count"] == 3
    assert result["estimated_elements"] == {"a": None, "e": None, "i": None}


def test_estimate_orbit_marks_multi_night_arc_as_estimated_status():
    result = estimate_orbit([
        {"ra": 10.0, "dec": 20.0, "time": "2026-01-01T00:00:00"},
        {"ra": 10.1, "dec": 20.1, "time": "2026-01-02T00:30:00"},
        {"ra": 10.2, "dec": 20.2, "time": "2026-01-03T01:00:00"},
    ])

    assert result is not None
    assert result["status"] == "estimated"
    assert result["time_span_hours"] > 24
