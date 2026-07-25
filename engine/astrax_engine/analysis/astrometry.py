"""
AstraX Engine — Astrometry
WCS coordinate transformations.
"""

import logging
from typing import Tuple, List

logger = logging.getLogger("astrax.engine.analysis.astrometry")


def pixel_to_world(wcs_header: dict, x: float, y: float) -> Tuple[float, float]:
    """Convert pixel coordinates to RA/Dec."""
    try:
        from astropy.wcs import WCS
        from astropy.io import fits
        
        # Reconstruct header
        header = fits.Header()
        for k, v in wcs_header.items():
            if isinstance(k, str) and len(k) <= 8:
                try:
                    header[k] = v
                except ValueError:
                    pass
                    
        w = WCS(header)
        if not w.is_celestial:
            return (None, None)
            
        ra, dec = w.all_pix2world(x, y, 0)
        return float(ra), float(dec)
        
    except Exception as e:
        logger.warning(f"WCS conversion failed: {e}")
        return (None, None)


def world_to_pixel(wcs_header: dict, ra: float, dec: float) -> Tuple[float, float]:
    """Convert RA/Dec to pixel coordinates."""
    try:
        from astropy.wcs import WCS
        from astropy.io import fits
        
        header = fits.Header()
        for k, v in wcs_header.items():
            if isinstance(k, str) and len(k) <= 8:
                try:
                    header[k] = v
                except ValueError:
                    pass
                    
        w = WCS(header)
        if not w.is_celestial:
            return (None, None)
            
        x, y = w.all_world2pix(ra, dec, 0)
        return float(x), float(y)
        
    except Exception as e:
        logger.warning(f"WCS conversion failed: {e}")
        return (None, None)
