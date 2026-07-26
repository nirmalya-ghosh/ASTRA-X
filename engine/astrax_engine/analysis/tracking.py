"""
AstraX Engine — Trajectory Tracking
Implements Kalman Filtering and Tracklet linking for moving objects.
"""

import logging
import numpy as np
from typing import List, Dict, Any

logger = logging.getLogger("astrax.engine.analysis.tracking")


class ObjectTracker:
    """
    Tracks multiple objects across frames using a Kalman Filter and Hungarian assignment.
    """
    def __init__(self, max_missing_frames: int = 3, distance_threshold: float = 50.0):
        self.tracks = []  # List of current active tracks
        self.next_track_id = 1
        self.max_missing_frames = max_missing_frames
        self.distance_threshold = distance_threshold
        
    def _create_kalman_filter(self, x: float, y: float):
        try:
            from filterpy.kalman import KalmanFilter
            
            # State: [x, y, dx, dy]
            kf = KalmanFilter(dim_x=4, dim_z=2)
            
            # Initial state
            kf.x = np.array([x, y, 0., 0.])
            
            # State transition matrix
            dt = 1.0  # Assuming 1 time step per frame for simplicity (could use actual exposure diff)
            kf.F = np.array([[1, 0, dt, 0],
                             [0, 1, 0, dt],
                             [0, 0, 1,  0],
                             [0, 0, 0,  1]])
                             
            # Measurement function (we only measure x, y)
            kf.H = np.array([[1, 0, 0, 0],
                             [0, 1, 0, 0]])
                             
            # Measurement noise
            kf.R *= 10.0
            
            # Process noise
            from filterpy.common import Q_discrete_white_noise
            kf.Q = Q_discrete_white_noise(dim=4, dt=dt, var=0.1)
            
            # Covariance
            kf.P *= 1000.0
            
            return kf
        except ImportError:
            return None

    def update(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Takes a list of detections for the current frame, updates tracks, 
        and returns the assigned track IDs.
        detections: list of dicts with 'x' and 'y'.
        """
        try:
            from scipy.optimize import linear_sum_assignment
        except ImportError:
            logger.warning("scipy not installed. Skipping track linking.")
            return []

        # Predict phase
        for track in self.tracks:
            if track['kf']:
                track['kf'].predict()
            track['age'] += 1
            track['missing_frames'] += 1

        # If no detections, just return
        if not detections:
            # Clean up old tracks
            self.tracks = [t for t in self.tracks if t['missing_frames'] <= self.max_missing_frames]
            return []

        # If no tracks, initialize them
        if not self.tracks:
            for det in detections:
                self._add_track(det)
            return self._get_active_tracks()

        # Build cost matrix between existing tracks and new detections
        cost_matrix = np.zeros((len(self.tracks), len(detections)))
        for i, track in enumerate(self.tracks):
            for j, det in enumerate(detections):
                if track['kf']:
                    pred_x, pred_y = track['kf'].x[0], track['kf'].x[1]
                else:
                    pred_x, pred_y = track['history'][-1]['x'], track['history'][-1]['y']
                
                dist = np.sqrt((pred_x - det['x'])**2 + (pred_y - det['y'])**2)
                cost_matrix[i, j] = dist

        # Hungarian assignment
        row_ind, col_ind = linear_sum_assignment(cost_matrix)
        
        # Update assigned tracks
        assigned_detections = set()
        for i, j in zip(row_ind, col_ind):
            if cost_matrix[i, j] <= self.distance_threshold:
                track = self.tracks[i]
                det = detections[j]
                
                if track['kf']:
                    track['kf'].update([det['x'], det['y']])
                
                track['history'].append(det)
                track['missing_frames'] = 0
                assigned_detections.add(j)

        # Create new tracks for unassigned detections
        for j, det in enumerate(detections):
            if j not in assigned_detections:
                self._add_track(det)

        # Remove dead tracks
        self.tracks = [t for t in self.tracks if t['missing_frames'] <= self.max_missing_frames]
        
        return self._get_active_tracks()

    def _add_track(self, det: Dict[str, Any]):
        track = {
            'id': self.next_track_id,
            'kf': self._create_kalman_filter(det['x'], det['y']),
            'history': [det],
            'age': 1,
            'missing_frames': 0
        }
        self.tracks.append(track)
        self.next_track_id += 1

    def _get_active_tracks(self) -> List[Dict[str, Any]]:
        # Return summary of tracks
        return [
            {
                'id': t['id'],
                'x': float(t['kf'].x[0]) if t['kf'] else t['history'][-1]['x'],
                'y': float(t['kf'].x[1]) if t['kf'] else t['history'][-1]['y'],
                'dx': float(t['kf'].x[2]) if t['kf'] else 0.0,
                'dy': float(t['kf'].x[3]) if t['kf'] else 0.0,
                'length': len(t['history']),
                'history': t['history']
            }
            for t in self.tracks
        ]
