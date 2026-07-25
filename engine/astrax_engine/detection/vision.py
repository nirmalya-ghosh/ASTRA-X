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
        
        # 1. Advanced Adaptive Thresholding (Finds local anomalies instead of global bright spots)
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 11, 2
        )
        
        # Optional morphological operations to close gaps
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        
        # 2. Find contours of potential anomalies
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Initialize HOG Descriptor for structural feature extraction
        winSize = (64,64)
        blockSize = (16,16)
        blockStride = (8,8)
        cellSize = (8,8)
        nbins = 9
        hog = cv2.HOGDescriptor(winSize, blockSize, blockStride, cellSize, nbins)
        
        sources = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area >= min_area:
                x, y, w, h = cv2.boundingRect(cnt)
                
                # Filter out massive blocks (likely background/errors)
                if w > img.shape[1]*0.5 or h > img.shape[0]*0.5:
                    continue
                    
                M = cv2.moments(cnt)
                cx = int(M['m10']/M['m00']) if M['m00'] != 0 else x + w//2
                cy = int(M['m01']/M['m00']) if M['m00'] != 0 else y + h//2
                
                # Extract HOG features if the object is large enough
                hog_features_found = False
                if w >= 64 and h >= 64:
                    roi = gray[y:y+h, x:x+w]
                    roi_resized = cv2.resize(roi, (64, 64))
                    h_features = hog.compute(roi_resized)
                    hog_features_found = True if h_features is not None else False
                
                mask = np.zeros(gray.shape, dtype=np.uint8)
                cv2.drawContours(mask, [cnt], -1, 255, -1)
                mean_val = cv2.mean(gray, mask=mask)[0]
                
                # Determine object type based on aspect ratio and edges
                aspect_ratio = float(w)/h if h > 0 else 1.0
                roundness = min(w, h) / max(w, h) if max(w, h) > 0 else 1.0
                
                notes = "Algorithmic Vision: "
                if roundness > 0.8:
                    notes += "Spherical anomaly (Crater/Asteroid profile). "
                elif aspect_ratio > 2.0 or aspect_ratio < 0.5:
                    notes += "Linear streak detected (Fast-moving object?). "
                
                if hog_features_found:
                    notes += "HOG structured features extracted."

                sources.append({
                    "x": cx,
                    "y": cy,
                    "bbox": (x, y, w, h),
                    "flux": mean_val * area,
                    "mag": 25 - 2.5 * np.log10(mean_val * area + 1), # mock magnitude
                    "snr": mean_val / 5.0, # mock SNR
                    "fwhm": max(w, h),
                    "sharpness": 0.5,
                    "roundness": roundness,
                    "notes": notes
                })
                
        logger.info(f"OpenCV HOG Vision detected {len(sources)} sources in {file_path}")
        return sources
        
    except Exception as e:
        logger.error(f"Local vision detection failed: {e}")
        return []
