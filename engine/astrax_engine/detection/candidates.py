"""
AstraX Engine — Candidate Generation & Linking
Cross-frame candidate linking and persistence scoring.
"""

import logging
import numpy as np
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger("astrax.engine.detection.candidates")


@dataclass
class DetectionPoint:
    frame_index: int
    x: float
    y: float
    flux: float
    bbox: tuple = None
    snr: float = 0.0
    motion_dx: float = 0.0
    motion_dy: float = 0.0


@dataclass
class CandidateTrack:
    id: int
    points: List[DetectionPoint] = field(default_factory=list)
    confidence: float = 0.0
    
    @property
    def persistence(self) -> int:
        return len(self.points)
        
    @property
    def latest_point(self) -> DetectionPoint:
        return self.points[-1] if self.points else None
        
    @property
    def velocity(self) -> Tuple[float, float]:
        if len(self.points) < 2:
            return (0.0, 0.0)
        p1, p2 = self.points[0], self.points[-1]
        dt = p2.frame_index - p1.frame_index
        if dt == 0:
            return (0.0, 0.0)
        return ((p2.x - p1.x) / dt, (p2.y - p1.y) / dt)


def link_candidates(
    frame_detections: Dict[int, List[Dict[str, Any]]], 
    max_distance: float = 10.0,
    min_persistence: int = 2
) -> List[CandidateTrack]:
    """
    Link detections across frames to form candidate tracks.
    """
    tracks: List[CandidateTrack] = []
    next_id = 1
    
    # Sort frames chronologically
    sorted_frames = sorted(frame_detections.keys())
    
    for frame_idx in sorted_frames:
        detections = frame_detections[frame_idx]
        unassigned_detections = list(detections)
        
        # Try to extend existing tracks
        for track in tracks:
            if not unassigned_detections:
                break
                
            last_point = track.latest_point
            
            # Predict next position based on velocity if we have at least 2 points
            if track.persistence >= 2:
                vx, vy = track.velocity
                dt = frame_idx - last_point.frame_index
                pred_x = last_point.x + vx * dt
                pred_y = last_point.y + vy * dt
            else:
                pred_x = last_point.x
                pred_y = last_point.y
                
            # Find closest detection within max_distance
            best_dist = max_distance
            best_det_idx = -1
            
            for i, det in enumerate(unassigned_detections):
                dist = np.sqrt((det['x'] - pred_x)**2 + (det['y'] - pred_y)**2)
                if dist < best_dist:
                    best_dist = dist
                    best_det_idx = i
                    
            if best_det_idx >= 0:
                det = unassigned_detections.pop(best_det_idx)
                track.points.append(
                    DetectionPoint(
                        frame_index=frame_idx,
                        x=det['x'],
                        y=det['y'],
                        flux=det.get('flux', 0.0),
                        snr=det.get('snr', 0.0),
                        motion_dx=det.get('motion_dx', 0.0),
                        motion_dy=det.get('motion_dy', 0.0)
                    )
                )
                
        # Create new tracks for remaining unassigned detections
        for det in unassigned_detections:
            new_track = CandidateTrack(id=next_id)
            new_track.points.append(
                DetectionPoint(
                    frame_index=frame_idx,
                    x=det['x'],
                    y=det['y'],
                    flux=det.get('flux', 0.0),
                    snr=det.get('snr', 0.0),
                    motion_dx=det.get('motion_dx', 0.0),
                    motion_dy=det.get('motion_dy', 0.0)
                )
            )
            tracks.append(new_track)
            next_id += 1
            
    # Filter by minimum persistence
    valid_tracks = [t for t in tracks if t.persistence >= min_persistence]
    logger.info(f"Generated {len(valid_tracks)} candidate tracks with persistence >= {min_persistence}")
    return valid_tracks
