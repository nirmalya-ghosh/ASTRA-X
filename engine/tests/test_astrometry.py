import pytest
from astropy.wcs import WCS
from astrax_engine.analysis.astrometry import pixel_to_world, world_to_pixel

@pytest.fixture
def mock_wcs():
    w = WCS(naxis=2)
    w.wcs.crpix = [50.5, 50.5]
    w.wcs.cdelt = np.array([-0.066667, 0.066667])
    w.wcs.crval = [0, -90]
    w.wcs.ctype = ["RA---AIR", "DEC--AIR"]
    return w

import numpy as np

def test_pixel_to_world(mock_wcs):
    ra, dec = pixel_to_world(mock_wcs, 50.5, 50.5)
    # The reference pixel should map to reference value
    np.testing.assert_almost_equal(ra, 0.0)
    np.testing.assert_almost_equal(dec, -90.0)

def test_world_to_pixel(mock_wcs):
    x, y = world_to_pixel(mock_wcs, 0.0, -90.0)
    np.testing.assert_almost_equal(x, 50.5)
    np.testing.assert_almost_equal(y, 50.5)
