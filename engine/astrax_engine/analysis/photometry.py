"""
AstraX Engine — Photometry
Aperture photometry and magnitude estimation.
"""

import logging
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
        
        # Measure
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
            
            # Instrumental magnitude
            mag = -2.5 * np.log10(net_flux) if net_flux > 0 else np.nan
            
            results.append({
                "x": positions[i][0],
                "y": positions[i][1],
                "raw_flux": float(raw_flux),
                "bg_flux": float(bg_flux),
                "net_flux": float(net_flux),
                "inst_mag": float(mag)
            })
            
        return results
        
    except ImportError:
        logger.error("photutils not installed. Cannot perform aperture photometry.")
        return []
