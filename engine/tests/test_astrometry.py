import numpy as np
import pytest
from astropy.wcs import WCS
from astrax_engine.analysis.astrometry import (
    fit_wcs_from_points,
    pixel_to_world,
    solve_blind,
    world_to_pixel,
)

@pytest.fixture
def mock_wcs():
    w = WCS(naxis=2)
    w.wcs.crpix = [50.5, 50.5]
    w.wcs.cdelt = np.array([-0.066667, 0.066667])
    w.wcs.crval = [0, -90]
    w.wcs.ctype = ["RA---AIR", "DEC--AIR"]
    return w

def test_pixel_to_world(mock_wcs):
    ra, dec = pixel_to_world(mock_wcs, 50.5, 50.5)
    # The reference pixel should map to reference value
    np.testing.assert_almost_equal(ra, 0.0)
    np.testing.assert_almost_equal(dec, -90.0)

def test_world_to_pixel(mock_wcs):
    x, y = world_to_pixel(mock_wcs, 0.0, -90.0)
    np.testing.assert_almost_equal(x, 50.5)
    np.testing.assert_almost_equal(y, 50.5)


def test_solve_blind_skips_without_api_key(monkeypatch, tmp_path):
    monkeypatch.delenv("ASTRAX_ASTROMETRY_NET_API_KEY", raising=False)
    image_path = tmp_path / "synthetic.fits"
    image_path.write_bytes(b"")

    result = solve_blind(image_path)

    assert result["status"] == "skipped"
    assert result["solver"] == "astrometry.net"


def test_fit_wcs_from_points_round_trips_synthetic_matches():
    pixels = [(10, 10), (80, 10), (10, 80), (80, 80)]
    sky = [(150.010, 2.010), (149.940, 2.010), (150.010, 2.080), (149.940, 2.080)]

    result = fit_wcs_from_points(pixels, sky, image_shape=(100, 100))

    assert result["status"] == "solved"
    ra, dec = pixel_to_world(result["wcs_header"], 10, 10)
    assert ra == pytest.approx(150.010, abs=0.01)
    assert dec == pytest.approx(2.010, abs=0.01)
