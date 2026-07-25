"""
AstraX Engine — Visualization Overlays
Draws candidate markers, trajectories, and annotations.
"""

import logging
import numpy as np

logger = logging.getLogger("astrax.engine.visualization.overlays")

def draw_markers(
    image_bytes: bytes,
    points: list[tuple[float, float]],
    radius: int = 5,
    color: tuple[int, int, int] = (0, 255, 0),
    thickness: int = 2
) -> bytes:
    """Draw circular markers on an image byte string."""
    try:
        import cv2
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        for (x, y) in points:
            cv2.circle(img, (int(x), int(y)), radius, color, thickness)
            
        success, encoded_image = cv2.imencode('.png', img)
        if success:
            return encoded_image.tobytes()
        return image_bytes
    except Exception as e:
        logger.error(f"Failed to draw markers: {e}")
        return image_bytes


def draw_trajectories(
    image_bytes: bytes,
    trajectories: list[list[tuple[float, float]]],
    color: tuple[int, int, int] = (255, 0, 0),
    thickness: int = 2
) -> bytes:
    """Draw line trajectories on an image byte string."""
    try:
        import cv2
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        for track in trajectories:
            if len(track) < 2:
                continue
            for i in range(len(track) - 1):
                pt1 = (int(track[i][0]), int(track[i][1]))
                pt2 = (int(track[i+1][0]), int(track[i+1][1]))
                cv2.line(img, pt1, pt2, color, thickness)
                
        success, encoded_image = cv2.imencode('.png', img)
        if success:
            return encoded_image.tobytes()
        return image_bytes
    except Exception as e:
        logger.error(f"Failed to draw trajectories: {e}")
        return image_bytes
