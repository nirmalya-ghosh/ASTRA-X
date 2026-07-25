"""
AstraX Engine — Vision Detection
Local algorithmic object detection for standard RGB/Grayscale images using OpenCV.
"""

import cv2
import numpy as np
from typing import List, Dict, Any
import logging

logger = logging.getLogger("astrax.engine.detection.vision")

def detect_vision_sources(file_path: str, threshold: int = 200, min_area: int = 10) -> List[Dict[str, Any]]:
    """
    Detect bright anomalies or objects in a standard image (JPG/PNG).
    Uses OpenCV contour detection as the primary local algorithm.
    """
    try:
        # Read image
        img = cv2.imread(file_path)
        if img is None:
            raise ValueError(f"Could not read image at {file_path}")
            
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply slight blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Threshold the image to find bright spots (asteroids/craters/anomalies)
        _, thresh = cv2.threshold(blurred, threshold, 255, cv2.THRESH_BINARY)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        sources = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area >= min_area:
                # Get bounding box and centroid
                x, y, w, h = cv2.boundingRect(cnt)
                M = cv2.moments(cnt)
                
                cx = int(M['m10']/M['m00']) if M['m00'] != 0 else x + w//2
                cy = int(M['m01']/M['m00']) if M['m00'] != 0 else y + h//2
                
                # Estimate fake flux/snr based on pixel intensity for ranking
                mask = np.zeros(gray.shape, dtype=np.uint8)
                cv2.drawContours(mask, [cnt], -1, 255, -1)
                mean_val = cv2.mean(gray, mask=mask)[0]
                
                sources.append({
                    "x": cx,
                    "y": cy,
                    "bbox": (x, y, w, h),
                    "flux": mean_val * area,
                    "mag": 25 - 2.5 * np.log10(mean_val * area + 1), # mock magnitude
                    "snr": mean_val / 5.0, # mock SNR
                    "fwhm": max(w, h),
                    "sharpness": 0.5,
                    "roundness": min(w, h) / max(w, h) if max(w, h) > 0 else 1.0
                })
                
        logger.info(f"OpenCV local vision detected {len(sources)} sources in {file_path}")
        return sources
        
    except Exception as e:
        logger.error(f"Local vision detection failed: {e}")
        return []
