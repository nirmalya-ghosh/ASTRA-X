import pytest
import numpy as np
from astrax_engine.analysis.photometry import extract_photometry

def test_extract_photometry_basic():
    # Create a 100x100 dummy image with a background of 10
    image = np.full((100, 100), 10.0)
    
    # Add a mock star at (50, 50)
    # 5x5 square of value 100
    image[48:53, 48:53] += 100.0
    
    # Call extraction
    flux, snr, background = extract_photometry(image, x=50.0, y=50.0, aperture_radius=3.0)
    
    assert background > 0
    assert flux > 0
    assert snr > 0

def test_extract_photometry_edge():
    image = np.full((100, 100), 10.0)
    # Test near the edge where annulus might go out of bounds
    flux, snr, background = extract_photometry(image, x=1.0, y=1.0, aperture_radius=2.0)
    assert background > 0
