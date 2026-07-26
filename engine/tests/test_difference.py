import numpy as np
import pytest

from astrax_engine.processing.difference import (
    alard_lupton_subtract,
    match_psf_gaussian,
    subtract_images,
    zogy_subtract,
)
from synthetic import gaussian_star_field


def test_direct_subtraction_preserves_transient_signal():
    reference = gaussian_star_field(stars=[(32, 32, 500, 1.5)])
    science = gaussian_star_field(stars=[(32, 32, 500, 1.5), (60, 55, 400, 1.5)])

    diff = subtract_images(science, reference)

    assert diff[55, 60] > 350
    assert abs(float(diff[32, 32])) < 1e-3


def test_gaussian_psf_matching_broadens_sharp_sources():
    image = gaussian_star_field(stars=[(48, 48, 1000, 1.0)])

    matched = match_psf_gaussian(image, source_fwhm=2.35, target_fwhm=5.0)

    assert matched.shape == image.shape
    assert matched[48, 48] < image[48, 48]
    assert np.isclose(matched.sum(), image.sum(), rtol=0.01)


def test_alard_lupton_subtract_reduces_seeing_mismatch_residuals():
    sharp = gaussian_star_field(stars=[(48, 48, 1000, 1.0)])
    broad = gaussian_star_field(stars=[(48, 48, 1000, 2.0)])

    direct = subtract_images(broad, sharp)
    matched = alard_lupton_subtract(
        broad,
        sharp,
        science_fwhm=4.71,
        reference_fwhm=2.35,
    )

    assert np.abs(matched).sum() < np.abs(direct).sum()


def test_zogy_subtract_returns_finite_difference_image():
    reference = gaussian_star_field(stars=[(30, 30, 300, 1.5)], noise=1.0)
    science = gaussian_star_field(stars=[(30, 30, 300, 1.5), (62, 60, 250, 1.5)], noise=1.0)

    diff = zogy_subtract(science, reference, science_fwhm=3.5, reference_fwhm=3.5)

    assert diff.shape == science.shape
    assert np.isfinite(diff).all()


def test_psf_methods_require_fwhm_values():
    image = gaussian_star_field()

    with pytest.raises(ValueError):
        subtract_images(image, image, method="zogy")
