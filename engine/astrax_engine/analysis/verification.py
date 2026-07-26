"""
AstraX Engine — Known Object Verification
Interfaces with Minor Planet Center (MPC) and JPL Horizons to cross-match detections.
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger("astrax.engine.analysis.verification")

def query_mpc(ra: float, dec: float, time: datetime, radius_arcsec: float = 30.0) -> List[Dict[str, Any]]:
    """
    Query the Minor Planet Center to find known objects near the given coordinates at a specific time.
    """
    try:
        from astroquery.mpc import MPC
        from astropy import units as u
        from astropy.coordinates import SkyCoord
        
        # Note: MPC cone search currently only works well for current epoch unless we use SkyBoT
        # For professional usage, IMCCE SkyBoT via astroquery.imcce is more reliable for historical cross-matching
        from astroquery.imcce import Skybot
        
        coord = SkyCoord(ra, dec, unit='deg', frame='icrs')
        # Time needs to be astropy Time object
        from astropy.time import Time
        t = Time(time)
        
        # Query SkyBoT for known objects within the radius at the exact observation time
        # We use a default observatory location if none provided (e.g., Geocentric '500')
        result = Skybot.cone_search(coord, radius_arcsec * u.arcsec, epoch=t, location='500')
        
        if result is None or len(result) == 0:
            return []
            
        matches = []
        for row in result:
            matches.append({
                "name": row['Name'],
                "number": row['Number'] if 'Number' in row.columns else None,
                "type": row['Type'] if 'Type' in row.columns else "Asteroid",
                "ra": float(row['RA']),
                "dec": float(row['DEC']),
                "vmag": float(row['V']) if 'V' in row.columns and not np.ma.is_masked(row['V']) else None,
                "distance_arcsec": float(row['centerdist']) if 'centerdist' in row.columns else None,
                "source": "IMCCE SkyBoT / MPC"
            })
            
        return matches

    except ImportError:
        logger.warning("astroquery is not installed. Cannot verify known objects.")
        return []
    except Exception as e:
        logger.error(f"Failed to query MPC/Skybot: {e}")
        return []

def query_jpl_horizons(object_name: str, time: datetime, location: str = '500') -> Optional[Dict[str, Any]]:
    """
    Get detailed ephemerides for a known object from JPL Horizons.
    """
    try:
        from astroquery.jplhorizons import Horizons
        from astropy.time import Time
        
        t = Time(time).jd
        
        obj = Horizons(id=object_name, location=location, epochs=t)
        eph = obj.ephemerides()
        
        if eph is None or len(eph) == 0:
            return None
            
        row = eph[0]
        return {
            "ra": float(row['RA']),
            "dec": float(row['DEC']),
            "vmag": float(row['V']) if 'V' in row.columns else None,
            "delta": float(row['delta']), # Distance from Earth in AU
            "r": float(row['r']), # Distance from Sun in AU
            "source": "JPL Horizons"
        }
        
    except ImportError:
        return None
    except Exception as e:
        logger.error(f"Failed to query JPL Horizons for {object_name}: {e}")
        return None

def verify_candidate(ra: float, dec: float, time: datetime, radius_arcsec: float = 30.0) -> Dict[str, Any]:
    """
    Cross-match a detection with known objects.
    Returns a verification summary.
    """
    if ra is None or dec is None or time is None:
        return {"status": "unverifiable", "reason": "Missing RA/DEC/Time"}
        
    matches = query_mpc(ra, dec, time, radius_arcsec)
    
    if not matches:
        return {
            "status": "unknown", 
            "reason": f"No known objects found within {radius_arcsec}\" radius",
            "matches": []
        }
        
    # Sort by distance
    matches.sort(key=lambda x: x.get('distance_arcsec', 999))
    best_match = matches[0]
    
    # If the distance is very close (e.g., < 5 arcsec), we consider it confirmed
    if best_match.get('distance_arcsec', 999) < 10.0:
        return {
            "status": "known_object",
            "object_name": best_match['name'],
            "distance_arcsec": best_match['distance_arcsec'],
            "vmag": best_match['vmag'],
            "matches": matches,
            "reason": f"Matches known object {best_match['name']} ({best_match['distance_arcsec']:.2f}\" away)"
        }
    else:
        return {
            "status": "possible_match",
            "object_name": best_match['name'],
            "distance_arcsec": best_match['distance_arcsec'],
            "matches": matches,
            "reason": f"Near known object {best_match['name']}, but distance is {best_match['distance_arcsec']:.2f}\""
        }
