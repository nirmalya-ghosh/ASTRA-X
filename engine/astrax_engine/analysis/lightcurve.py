"""
AstraX Engine — Lightcurve Analysis

Lightcurve construction and period analysis from multi-frame observations.
Inspired by astrokit's lightcurve reduction pipeline.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

logger = logging.getLogger("astrax.engine.analysis.lightcurve")


@dataclass
class LightcurvePoint:
    """Single photometric measurement in time."""
    time_jd: float       # Julian Date
    magnitude: float
    mag_error: float
    flux: float
    snr: float
    frame_index: int
    filter_name: str = ""


@dataclass
class LightcurveResult:
    """Complete lightcurve analysis result."""
    points: list[LightcurvePoint] = field(default_factory=list)
    n_points: int = 0
    mag_mean: float = 0.0
    mag_std: float = 0.0
    mag_range: float = 0.0
    best_period: Optional[float] = None
    period_power: Optional[float] = None
    frequency_grid: Optional[list[float]] = None
    power_spectrum: Optional[list[float]] = None


def build_lightcurve(
    photometry_results: list[dict],
    times_jd: list[float],
    frame_indices: list[int],
    filter_names: Optional[list[str]] = None,
) -> LightcurveResult:
    """
    Build a lightcurve from photometry results across multiple frames.

    Parameters
    ----------
    photometry_results : list of dicts with 'inst_mag', 'mag_unc', 'net_flux', 'snr'
    times_jd : Julian Date for each frame
    frame_indices : frame indices
    filter_names : optional filter names per frame
    """
    if not photometry_results or not times_jd:
        return LightcurveResult()

    points = []
    for i, phot in enumerate(photometry_results):
        mag = phot.get("inst_mag") or phot.get("cal_mag", np.nan)
        mag_err = phot.get("mag_unc", 0.0)
        flux = phot.get("net_flux", 0.0)
        snr = phot.get("snr", 0.0)
        t = times_jd[i] if i < len(times_jd) else 0.0
        fi = frame_indices[i] if i < len(frame_indices) else i
        fn = filter_names[i] if filter_names and i < len(filter_names) else ""

        if not np.isnan(mag):
            points.append(LightcurvePoint(
                time_jd=t, magnitude=mag, mag_error=mag_err,
                flux=flux, snr=snr, frame_index=fi, filter_name=fn,
            ))

    if not points:
        return LightcurveResult()

    mags = np.array([p.magnitude for p in points])
    result = LightcurveResult(
        points=points,
        n_points=len(points),
        mag_mean=round(float(np.mean(mags)), 4),
        mag_std=round(float(np.std(mags)), 4),
        mag_range=round(float(np.ptp(mags)), 4),
    )
    return result


def analyze_period(
    lightcurve: LightcurveResult,
    min_period: float = 0.01,
    max_period: float = 10.0,
    n_frequencies: int = 10000,
) -> LightcurveResult:
    """
    Run Lomb-Scargle periodogram to find the best period.

    Parameters
    ----------
    lightcurve : LightcurveResult with points
    min_period : minimum period to search (days)
    max_period : maximum period to search (days)
    n_frequencies : number of frequency samples
    """
    if lightcurve.n_points < 3:
        logger.warning("Need at least 3 points for period analysis.")
        return lightcurve

    try:
        from astropy.timeseries import LombScargle

        times = np.array([p.time_jd for p in lightcurve.points])
        mags = np.array([p.magnitude for p in lightcurve.points])
        errors = np.array([p.mag_error for p in lightcurve.points])
        errors = np.where(errors > 0, errors, 0.01)

        # Normalize times
        t0 = times.min()
        t_norm = times - t0

        min_freq = 1.0 / max_period
        max_freq = 1.0 / min_period
        frequency = np.linspace(min_freq, max_freq, n_frequencies)

        ls = LombScargle(t_norm, mags, errors)
        power = ls.power(frequency)

        best_idx = np.argmax(power)
        best_freq = frequency[best_idx]
        best_period = 1.0 / best_freq
        best_power = power[best_idx]

        lightcurve.best_period = round(float(best_period), 6)
        lightcurve.period_power = round(float(best_power), 4)
        lightcurve.frequency_grid = [round(float(f), 6) for f in frequency[::max(1, len(frequency) // 500)]]
        lightcurve.power_spectrum = [round(float(p), 4) for p in power[::max(1, len(power) // 500)]]

        logger.info("Period analysis: best period = %.4f days (power = %.3f)", best_period, best_power)
        return lightcurve

    except ImportError:
        logger.error("astropy.timeseries not available for Lomb-Scargle.")
        return lightcurve
    except Exception as e:
        logger.error("Period analysis failed: %s", e)
        return lightcurve


def phase_fold(
    lightcurve: LightcurveResult,
    period: Optional[float] = None,
    epoch: Optional[float] = None,
) -> list[dict]:
    """
    Phase-fold the lightcurve at a given period.

    Returns list of {phase, magnitude, mag_error} dicts.
    """
    p = period or lightcurve.best_period
    if not p or p <= 0:
        return []

    times = np.array([pt.time_jd for pt in lightcurve.points])
    mags = np.array([pt.magnitude for pt in lightcurve.points])
    errs = np.array([pt.mag_error for pt in lightcurve.points])

    t0 = epoch if epoch else times.min()
    phases = ((times - t0) / p) % 1.0

    # Sort by phase
    order = np.argsort(phases)
    return [
        {"phase": round(float(phases[i]), 5),
         "magnitude": round(float(mags[i]), 4),
         "mag_error": round(float(errs[i]), 4)}
        for i in order
    ]
