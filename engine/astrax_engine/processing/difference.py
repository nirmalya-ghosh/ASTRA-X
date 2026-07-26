"""
AstraX Engine — Difference Imaging
Creates reference frames and performs direct, PSF-matched, and ZOGY-style subtraction.
"""

import logging
import numpy as np
from typing import List, Optional, Tuple

logger = logging.getLogger("astrax.engine.processing.difference")

def create_median_reference(image_sequence: List[np.ndarray]) -> np.ndarray:
    """
    Creates a median reference frame from a sequence of aligned images.
    """
    if not image_sequence:
        raise ValueError("Empty image sequence provided for reference creation.")
        
    logger.info(f"Creating median reference frame from {len(image_sequence)} images.")
    # Stack along a new axis and take the median
    stacked = np.stack(image_sequence, axis=0)
    reference = np.median(stacked, axis=0)
    return reference

def estimate_background_sigma(image: np.ndarray) -> float:
    """Robustly estimate image noise using sigma-clipped statistics."""
    try:
        from astropy.stats import sigma_clipped_stats

        _, _, std = sigma_clipped_stats(image, sigma=3.0)
        return float(std)
    except Exception:
        return float(np.nanstd(image))


def _gaussian_kernel_sigma(source_fwhm: float, target_fwhm: float) -> float:
    """Return the Gaussian kernel sigma needed to broaden source to target FWHM."""
    if source_fwhm <= 0 or target_fwhm <= 0:
        raise ValueError("FWHM values must be positive")
    source_sigma = source_fwhm / 2.354820045
    target_sigma = target_fwhm / 2.354820045
    kernel_var = max(target_sigma**2 - source_sigma**2, 0.0)
    return float(np.sqrt(kernel_var))


def match_psf_gaussian(
    image: np.ndarray,
    source_fwhm: float,
    target_fwhm: float,
) -> np.ndarray:
    """
    Match a narrower Gaussian PSF to a broader target PSF.

    This is a lightweight Alard-Lupton-inspired basis approximation suitable for
    Render-tier deployments. Full spatially varying kernels can be layered on top
    of this API later without changing callers.
    """
    from scipy.ndimage import gaussian_filter

    sigma = _gaussian_kernel_sigma(source_fwhm, target_fwhm)
    if sigma == 0:
        return image.astype(np.float32, copy=True)
    return gaussian_filter(image.astype(np.float32), sigma=sigma, mode="reflect")


def alard_lupton_subtract(
    science_image: np.ndarray,
    reference_image: np.ndarray,
    *,
    science_fwhm: float,
    reference_fwhm: float,
) -> np.ndarray:
    """
    PSF-match images with a Gaussian kernel and subtract reference from science.

    The sharper image is convolved to the broader seeing before subtraction,
    mirroring the central idea of Alard-Lupton image subtraction.
    """
    if science_image.shape != reference_image.shape:
        raise ValueError(f"Shape mismatch: science {science_image.shape} vs ref {reference_image.shape}")

    science = science_image.astype(np.float32)
    reference = reference_image.astype(np.float32)
    target_fwhm = max(science_fwhm, reference_fwhm)

    matched_science = match_psf_gaussian(science, science_fwhm, target_fwhm)
    matched_reference = match_psf_gaussian(reference, reference_fwhm, target_fwhm)
    return matched_science - matched_reference


def zogy_subtract(
    science_image: np.ndarray,
    reference_image: np.ndarray,
    *,
    science_fwhm: float,
    reference_fwhm: float,
    science_noise: Optional[float] = None,
    reference_noise: Optional[float] = None,
) -> np.ndarray:
    """
    Produce a ZOGY-style optimal difference image for Gaussian PSFs.

    This implements the Fourier-domain weighting from Zackay, Ofek & Gal-Yam in
    a compact form using normalized Gaussian PSFs. It is intentionally limited to
    constant PSF/noise across the frame, which keeps it robust for small datasets.
    """
    if science_image.shape != reference_image.shape:
        raise ValueError(f"Shape mismatch: science {science_image.shape} vs ref {reference_image.shape}")

    science = science_image.astype(np.float32)
    reference = reference_image.astype(np.float32)
    science_noise = science_noise or estimate_background_sigma(science)
    reference_noise = reference_noise or estimate_background_sigma(reference)

    height, width = science.shape
    yy, xx = np.indices((height, width), dtype=np.float32)
    cx = width // 2
    cy = height // 2

    def gaussian_psf(fwhm: float) -> np.ndarray:
        sigma = max(fwhm / 2.354820045, 1e-6)
        psf = np.exp(-0.5 * (((xx - cx) / sigma) ** 2 + ((yy - cy) / sigma) ** 2))
        psf /= psf.sum() + 1e-12
        return np.fft.ifftshift(psf)

    psf_s = gaussian_psf(science_fwhm)
    psf_r = gaussian_psf(reference_fwhm)
    s_hat = np.fft.fft2(science)
    r_hat = np.fft.fft2(reference)
    ps_hat_s = np.fft.fft2(psf_s)
    ps_hat_r = np.fft.fft2(psf_r)

    denom = np.sqrt(
        (science_noise**2) * np.abs(ps_hat_r) ** 2
        + (reference_noise**2) * np.abs(ps_hat_s) ** 2
        + 1e-12
    )
    diff_hat = (ps_hat_r * s_hat - ps_hat_s * r_hat) / denom
    return np.fft.ifft2(diff_hat).real.astype(np.float32)


def subtract_images(
    science_image: np.ndarray,
    reference_image: np.ndarray,
    *,
    method: str = "direct",
    science_fwhm: Optional[float] = None,
    reference_fwhm: Optional[float] = None,
) -> np.ndarray:
    """
    Subtracts the reference image from the science image.
    """
    if science_image.shape != reference_image.shape:
        raise ValueError(f"Shape mismatch: science {science_image.shape} vs ref {reference_image.shape}")

    if method == "direct":
        return science_image.astype(np.float32) - reference_image.astype(np.float32)
    if method in {"alard-lupton", "psf-match"}:
        if science_fwhm is None or reference_fwhm is None:
            raise ValueError("science_fwhm and reference_fwhm are required for PSF-matched subtraction")
        return alard_lupton_subtract(
            science_image,
            reference_image,
            science_fwhm=science_fwhm,
            reference_fwhm=reference_fwhm,
        )
    if method == "zogy":
        if science_fwhm is None or reference_fwhm is None:
            raise ValueError("science_fwhm and reference_fwhm are required for ZOGY subtraction")
        return zogy_subtract(
            science_image,
            reference_image,
            science_fwhm=science_fwhm,
            reference_fwhm=reference_fwhm,
        )
    raise ValueError(f"Unknown subtraction method: {method}")

def detect_transients(diff_image: np.ndarray, sigma_thresh: float = 5.0) -> List[Tuple[float, float, float]]:
    """
    Detects transients in a difference image.
    Returns a list of (x, y, snr) tuples.
    """
    from astropy.stats import sigma_clipped_stats
    
    mean, median, std = sigma_clipped_stats(diff_image, sigma=3.0)
    
    # Threshold the difference image
    threshold = median + (sigma_thresh * std)
    
    # Find peaks above threshold
    try:
        from photutils.detection import find_peaks
        peaks = find_peaks(diff_image, threshold=threshold, box_size=5)
        
        transients = []
        if peaks is not None:
            for row in peaks:
                x = float(row['x_peak'])
                y = float(row['y_peak'])
                peak_val = float(row['peak_value'])
                snr = (peak_val - median) / (std + 1e-10)
                transients.append((x, y, snr))
                
        return transients
    except ImportError:
        logger.warning("photutils not installed. Skipping peak finding.")
        return []
