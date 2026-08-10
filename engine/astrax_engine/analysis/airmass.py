"""
AstraX Engine — Airmass & Atmospheric Corrections

Ported from astrokit's airmass.py and corrections.py.
Computes airmass from observation metadata and applies
atmospheric extinction corrections.
"""

from __future__ import annotations

import logging
from typing import Optional
from datetime import datetime

import numpy as np

logger = logging.getLogger("astrax.engine.analysis.airmass")


def compute_airmass(
    latitude: float,
    longitude: float,
    elevation: float,
    obs_time: datetime | str,
    ra: float,
    dec: float,
) -> Optional[float]:
    """
    Compute airmass for a celestial target at given observer location and time.

    Ported from astrokit's compute_airmass_for_point function.
    Uses the sec(z) formula via astropy AltAz transformation.

    Parameters
    ----------
    latitude : observer latitude in degrees
    longitude : observer longitude in degrees
    elevation : observer elevation in meters
    obs_time : observation datetime or ISO string
    ra : target right ascension in degrees
    dec : target declination in degrees

    Returns
    -------
    float : airmass (sec z), or None on failure
    """
    try:
        from astropy import units as u
        from astropy.time import Time
        from astropy.coordinates import SkyCoord, EarthLocation, AltAz

        coord = SkyCoord(ra * u.deg, dec * u.deg, frame='icrs')
        loc = EarthLocation(lat=latitude * u.deg, lon=longitude * u.deg, height=elevation)

        if isinstance(obs_time, str):
            time = Time(obs_time, format='iso')
        else:
            time = Time(obs_time.strftime('%Y-%m-%d %H:%M:%SZ'), format='iso')

        altaz = coord.transform_to(AltAz(obstime=time, location=loc))
        airmass_val = float(altaz.secz)

        if airmass_val < 1.0 or airmass_val > 10.0:
            logger.warning("Airmass %.2f out of typical range [1, 10]", airmass_val)

        return round(airmass_val, 4)

    except ImportError:
        logger.error("astropy not installed for airmass computation.")
        return None
    except Exception as e:
        logger.error("Airmass computation failed: %s", e)
        return None


def apply_extinction_correction(
    magnitude: float,
    airmass: float,
    extinction_coeff: float,
) -> float:
    """
    Apply atmospheric extinction correction to a magnitude.

    m_corrected = m_observed - k * X

    Parameters
    ----------
    magnitude : observed instrumental magnitude
    airmass : observation airmass
    extinction_coeff : extinction coefficient (mag/airmass) for the filter band
    """
    return magnitude - extinction_coeff * airmass


def get_extinction_coefficients() -> dict[str, float]:
    """
    Return typical extinction coefficients for common filter bands.
    Values are approximate and site-dependent.
    """
    return {
        "U": 0.55,
        "B": 0.30,
        "V": 0.15,
        "R": 0.10,
        "I": 0.05,
        "g": 0.20,
        "r": 0.10,
        "i": 0.05,
        "z": 0.04,
        "J": 0.05,
        "H": 0.03,
        "K": 0.05,
    }


def compute_jd(obs_time: datetime | str) -> Optional[float]:
    """
    Convert observation time to Julian Date.
    Ported from astrokit's corrections.py.
    """
    try:
        from astropy.time import Time
        if isinstance(obs_time, str):
            t = Time(obs_time, format='iso')
        else:
            t = Time(obs_time)
        return float(t.jd)
    except Exception as e:
        logger.error("JD conversion failed: %s", e)
        return None


def estimate_temperature_from_color(b_mag: float, v_mag: float) -> Optional[float]:
    """
    Estimate stellar effective temperature from B-V color index.
    Ported from astrokit's stellar_color.py.

    Uses the Ballesteros (2012) formula:
    T = 4600 * (1/(0.92*(B-V) + 1.7) + 1/(0.92*(B-V) + 0.62))
    """
    try:
        bv = b_mag - v_mag
        temp = 4600.0 * (1.0 / (0.92 * bv + 1.7) + 1.0 / (0.92 * bv + 0.62))
        return round(temp, 0)
    except (ZeroDivisionError, ValueError):
        return None
