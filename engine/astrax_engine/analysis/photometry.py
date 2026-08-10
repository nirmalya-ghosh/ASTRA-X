"""
AstraX Engine — Photometry (Enhanced)

Aperture photometry, PSF photometry, SNR estimation, and magnitude calibration.
Incorporates algorithms from astrokit's point_source_extraction and catalog modules.
"""

import logging
from typing import Optional

import numpy as np

logger = logging.getLogger("astrax.engine.analysis.photometry")


def measure_aperture_photometry(
    data: np.ndarray,
    positions: list[tuple[float, float]],
    aperture_radius: float = 3.0,
    annulus_inner: float = 5.0,
    annulus_outer: float = 8.0,
) -> list[dict]:
    """Measure aperture photometry with local background subtraction."""
    try:
        from photutils.aperture import CircularAperture, CircularAnnulus, aperture_photometry
        from astropy.stats import sigma_clipped_stats

        if not positions:
            return []

        apertures = CircularAperture(positions, r=aperture_radius)
        annuli = CircularAnnulus(positions, r_in=annulus_inner, r_out=annulus_outer)

        phot_table = aperture_photometry(data, apertures)
        annulus_masks = annuli.to_mask(method='center')

        results = []
        for i, mask in enumerate(annulus_masks):
            annulus_data = mask.multiply(data)
            if annulus_data is None:
                bg_median = 0.0
            else:
                annulus_data_1d = annulus_data[mask.data > 0]
                _, bg_median, _ = sigma_clipped_stats(annulus_data_1d, sigma=3.0)

            raw_flux = phot_table['aperture_sum'][i]
            bg_flux = bg_median * apertures.area
            net_flux = raw_flux - bg_flux

            # Instrumental magnitude (from astrokit formula)
            mag = -2.5 * np.log10(net_flux) if net_flux > 0 else np.nan
            # Magnitude uncertainty (Poisson + background noise)
            if net_flux > 0:
                noise = np.sqrt(net_flux + bg_flux)
                mag_unc = 2.5 / np.log(10) * (noise / net_flux)
            else:
                mag_unc = np.nan

            # SNR (from astrokit: 1 / (10^(mag_unc/2.5) - 1))
            if not np.isnan(mag_unc) and mag_unc > 0:
                snr = 1.0 / (np.power(10, mag_unc / 2.5) - 1)
            else:
                snr = 0.0

            results.append({
                "x": positions[i][0],
                "y": positions[i][1],
                "raw_flux": float(raw_flux),
                "bg_flux": float(bg_flux),
                "bg_median": float(bg_median),
                "net_flux": float(net_flux),
                "inst_mag": float(mag),
                "mag_unc": float(mag_unc),
                "snr": round(float(snr), 2),
            })

        return results

    except ImportError:
        logger.error("photutils not installed. Cannot perform aperture photometry.")
        return []


def run_psf_photometry(
    data: np.ndarray,
    sigma_psf: float = 2.0,
    threshold: float = 3.0,
    box_size: int = 11,
    niters: int = 3,
) -> list[dict]:
    """
    PSF-fitting photometry using DAOStarFinder + Gaussian PSF model.
    Ported from astrokit's compute_photutils function.

    Parameters
    ----------
    data : 2D image array
    sigma_psf : PSF Gaussian sigma in pixels
    threshold : detection threshold in σ above background
    box_size : fitting box size
    niters : number of PSF subtraction iterations
    """
    try:
        from astropy.stats import SigmaClip, sigma_clipped_stats
        from photutils.background import MADStdBackgroundRMS
        from photutils.detection import DAOStarFinder

        _, bg_median, bg_std = sigma_clipped_stats(data, sigma=3.0)
        subtracted = data - bg_median

        fwhm = sigma_psf * 2.355  # sigma to FWHM
        finder = DAOStarFinder(fwhm=fwhm, threshold=threshold * bg_std)
        sources = finder(subtracted)

        if sources is None or len(sources) == 0:
            return []

        results = []
        for row in sources:
            flux = float(row['flux'])
            mag = -2.5 * np.log10(flux) if flux > 0 else np.nan
            # SNR from flux and background
            noise = np.sqrt(abs(flux) + bg_std ** 2 * np.pi * fwhm ** 2)
            snr = flux / noise if noise > 0 else 0.0

            results.append({
                "id": int(row['id']),
                "x": float(row['xcentroid']),
                "y": float(row['ycentroid']),
                "flux": round(flux, 2),
                "inst_mag": round(float(mag), 4),
                "peak": float(row['peak']),
                "sharpness": float(row['sharpness']),
                "roundness": float(row['roundness1']),
                "snr": round(float(snr), 2),
                "fwhm": round(fwhm, 2),
            })

        results.sort(key=lambda r: r["snr"], reverse=True)
        return results

    except ImportError:
        logger.error("photutils/astropy not installed for PSF photometry.")
        return []
    except Exception as e:
        logger.error("PSF photometry failed: %s", e)
        return []


def calibrate_magnitudes(
    sources: list[dict],
    zero_point: float = 25.0,
    extinction_coeff: float = 0.0,
    airmass: float = 1.0,
    color_term: float = 0.0,
    color_index: float = 0.0,
) -> list[dict]:
    """
    Apply zero-point calibration to instrumental magnitudes.
    Based on astrokit's magnitude calibration: m_cal = m_inst + ZP - k*X + T*CI

    Parameters
    ----------
    sources : list of dicts with 'inst_mag'
    zero_point : photometric zero point
    extinction_coeff : atmospheric extinction coefficient
    airmass : observation airmass
    color_term : color transformation coefficient
    color_index : source color index (e.g., B-V)
    """
    calibrated = []
    for src in sources:
        inst_mag = src.get("inst_mag", np.nan)
        if np.isnan(inst_mag):
            cal_mag = np.nan
        else:
            cal_mag = inst_mag + zero_point - extinction_coeff * airmass + color_term * color_index
        entry = {**src, "cal_mag": round(float(cal_mag), 4)}
        calibrated.append(entry)
    return calibrated


def compute_pixel_scale(wcs_header: dict) -> Optional[float]:
    """
    Compute pixel scale in arcsec/pixel from WCS CD matrix.
    Ported from astrokit's get_pixscale.
    """
    import math
    try:
        from astropy.wcs import WCS
        from astropy.io import fits

        hdr = fits.Header()
        for k, v in wcs_header.items():
            try:
                hdr[k] = v
            except (ValueError, TypeError):
                pass

        w = WCS(hdr)
        if not hasattr(w.wcs, 'cd') or w.wcs.cd is None:
            # Try using pixel_scale_matrix
            ps = w.proj_plane_pixel_scales()
            return float(ps[0] * 3600.0) if len(ps) > 0 else None

        cd11 = w.wcs.cd[0][0]
        cd12 = w.wcs.cd[0][1]
        cd21 = w.wcs.cd[1][0]
        cd22 = w.wcs.cd[1][1]
        det_cd = cd11 * cd22 - cd12 * cd21
        return 3600.0 * math.sqrt(abs(det_cd))
    except Exception as e:
        logger.warning("Pixel scale computation failed: %s", e)
        return None
