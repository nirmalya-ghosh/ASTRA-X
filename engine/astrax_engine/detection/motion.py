"""
AstraX Engine — Motion Detection
Frame differencing, optical flow, and trajectory analysis.
"""

import logging
from typing import Optional
import numpy as np

logger = logging.getLogger("astrax.engine.detection.motion")


def detect_motion_frame_diff(
    frame1: np.ndarray,
    frame2: np.ndarray,
    threshold: float = 3.0,
    min_area: int = 5,
) -> list[dict]:
    """
    Detect motion via frame differencing.

    Args:
        frame1: First aligned frame
        frame2: Second aligned frame
        threshold: Detection threshold in sigma
        min_area: Minimum blob area in pixels

    Returns:
        List of motion candidate dicts
    """
    from astropy.stats import sigma_clipped_stats
    from scipy import ndimage

    # Compute difference
    diff = frame2.astype(np.float64) - frame1.astype(np.float64)

    # Statistics of difference image
    _, median, std = sigma_clipped_stats(diff, sigma=3.0)

    # Threshold
    binary = np.abs(diff - median) > threshold * std

    # Label connected components
    labeled, num_features = ndimage.label(binary)

    candidates = []
    for i in range(1, num_features + 1):
        mask = labeled == i
        area = np.sum(mask)

        if area < min_area:
            continue

        # Centroid
        cy, cx = ndimage.center_of_mass(np.abs(diff) * mask)

        # Flux in difference image
        flux = np.sum(diff[mask])

        candidates.append({
            "x": float(cx),
            "y": float(cy),
            "area": int(area),
            "flux_diff": float(flux),
            "peak_diff": float(np.max(np.abs(diff[mask]))),
            "method": "frame_diff",
        })

    logger.info(f"Frame differencing: {len(candidates)} motion candidates")
    return candidates


def optical_flow_lucas_kanade(
    frame1: np.ndarray,
    frame2: np.ndarray,
    points: list[tuple] = None,
    win_size: int = 15,
) -> list[dict]:
    """
    Lucas-Kanade optical flow for sparse motion estimation.

    Args:
        frame1: First frame (float64)
        frame2: Second frame (float64)
        points: Points to track [(x, y), ...]. If None, auto-detect.
        win_size: Window size for flow computation

    Returns:
        List of motion vectors
    """
    import cv2

    # Convert to uint8 for OpenCV
    def to_uint8(img):
        vmin, vmax = np.percentile(img, [1, 99])
        clipped = np.clip((img - vmin) / (vmax - vmin + 1e-10), 0, 1)
        return (clipped * 255).astype(np.uint8)

    img1 = to_uint8(frame1)
    img2 = to_uint8(frame2)

    # Detect features if not provided
    if points is None:
        features = cv2.goodFeaturesToTrack(
            img1, maxCorners=500, qualityLevel=0.01,
            minDistance=10, blockSize=7
        )
        if features is None:
            return []
        p0 = features.reshape(-1, 1, 2).astype(np.float32)
    else:
        p0 = np.array(points, dtype=np.float32).reshape(-1, 1, 2)

    # Calculate optical flow
    lk_params = dict(
        winSize=(win_size, win_size),
        maxLevel=3,
        criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01)
    )

    p1, status, error = cv2.calcOpticalFlowPyrLK(img1, img2, p0, None, **lk_params)

    if p1 is None:
        return []

    # Filter good tracks
    good_mask = status.flatten() == 1
    p0_good = p0[good_mask].reshape(-1, 2)
    p1_good = p1[good_mask].reshape(-1, 2)

    motions = []
    for (x0, y0), (x1, y1) in zip(p0_good, p1_good):
        dx = float(x1 - x0)
        dy = float(y1 - y0)
        speed = np.sqrt(dx**2 + dy**2)
        angle = np.degrees(np.arctan2(dy, dx))

        motions.append({
            "x0": float(x0), "y0": float(y0),
            "x1": float(x1), "y1": float(y1),
            "dx": dx, "dy": dy,
            "speed": float(speed),
            "angle": float(angle),
            "method": "lucas_kanade",
        })

    return motions


def optical_flow_farneback(
    frame1: np.ndarray,
    frame2: np.ndarray,
    motion_threshold: float = 1.0,
) -> tuple[np.ndarray, list[dict]]:
    """
    Dense optical flow using Farneback method.

    Args:
        frame1: First frame
        frame2: Second frame
        motion_threshold: Minimum motion magnitude to report

    Returns:
        (flow_field, motion_candidates)
    """
    import cv2

    def to_uint8(img):
        vmin, vmax = np.percentile(img, [1, 99])
        clipped = np.clip((img - vmin) / (vmax - vmin + 1e-10), 0, 1)
        return (clipped * 255).astype(np.uint8)

    img1 = to_uint8(frame1)
    img2 = to_uint8(frame2)

    flow = cv2.calcOpticalFlowFarneback(
        img1, img2, None,
        pyr_scale=0.5, levels=3, winsize=15,
        iterations=3, poly_n=5, poly_sigma=1.2,
        flags=0
    )

    # Compute magnitude and angle
    magnitude = np.sqrt(flow[..., 0]**2 + flow[..., 1]**2)

    # Find regions with significant motion
    from scipy import ndimage

    motion_mask = magnitude > motion_threshold
    labeled, num_features = ndimage.label(motion_mask)

    candidates = []
    for i in range(1, num_features + 1):
        mask = labeled == i
        area = np.sum(mask)
        if area < 3:
            continue

        cy, cx = ndimage.center_of_mass(magnitude * mask)
        avg_dx = float(np.mean(flow[mask, 0]))
        avg_dy = float(np.mean(flow[mask, 1]))
        avg_speed = float(np.mean(magnitude[mask]))
        angle = float(np.degrees(np.arctan2(avg_dy, avg_dx)))

        candidates.append({
            "x": float(cx),
            "y": float(cy),
            "dx": avg_dx,
            "dy": avg_dy,
            "speed": avg_speed,
            "angle": angle,
            "area": int(area),
            "max_speed": float(np.max(magnitude[mask])),
            "method": "farneback",
        })

    return flow, candidates


def detect_motion_dog(
    frame1: np.ndarray,
    frame2: np.ndarray,
    sigma_low: float = 1.0,
    sigma_high: float = 3.0,
    threshold: float = 3.0,
) -> list[dict]:
    """
    Difference of Gaussians motion detection.

    Applies DoG to each frame independently, then differences
    the filtered frames to find moving objects.
    """
    from scipy.ndimage import gaussian_filter
    from scipy import ndimage
    from astropy.stats import sigma_clipped_stats

    # DoG for each frame
    dog1 = gaussian_filter(frame1, sigma_low) - gaussian_filter(frame1, sigma_high)
    dog2 = gaussian_filter(frame2, sigma_low) - gaussian_filter(frame2, sigma_high)

    # Difference of DoGs
    diff = dog2 - dog1
    _, median, std = sigma_clipped_stats(diff, sigma=3.0)

    binary = np.abs(diff - median) > threshold * std
    labeled, num_features = ndimage.label(binary)

    candidates = []
    for i in range(1, num_features + 1):
        mask = labeled == i
        area = np.sum(mask)
        if area < 3:
            continue

        cy, cx = ndimage.center_of_mass(np.abs(diff) * mask)
        candidates.append({
            "x": float(cx),
            "y": float(cy),
            "area": int(area),
            "flux_diff": float(np.sum(diff[mask])),
            "method": "dog",
        })

    return candidates


def fit_trajectory(
    positions: list[tuple[float, float]],
    times: list[float] = None,
) -> dict:
    """
    Fit a trajectory to a series of positions.

    Args:
        positions: List of (x, y) positions
        times: Optional list of timestamps

    Returns:
        Trajectory parameters (velocity, direction, R², etc.)
    """
    if len(positions) < 2:
        return {"valid": False, "reason": "insufficient_points"}

    xs = np.array([p[0] for p in positions])
    ys = np.array([p[1] for p in positions])

    if times is None:
        times = np.arange(len(positions), dtype=np.float64)
    else:
        times = np.array(times, dtype=np.float64)

    # Linear fit
    from numpy.polynomial import polynomial as P

    # Fit x(t) and y(t)
    coeffs_x = np.polyfit(times, xs, 1)
    coeffs_y = np.polyfit(times, ys, 1)

    vx = coeffs_x[0]  # pixels per time unit
    vy = coeffs_y[0]

    # Residuals
    x_pred = np.polyval(coeffs_x, times)
    y_pred = np.polyval(coeffs_y, times)

    ss_res_x = np.sum((xs - x_pred) ** 2)
    ss_tot_x = np.sum((xs - np.mean(xs)) ** 2) + 1e-10
    r2_x = 1 - ss_res_x / ss_tot_x

    ss_res_y = np.sum((ys - y_pred) ** 2)
    ss_tot_y = np.sum((ys - np.mean(ys)) ** 2) + 1e-10
    r2_y = 1 - ss_res_y / ss_tot_y

    speed = np.sqrt(vx**2 + vy**2)
    angle = np.degrees(np.arctan2(vy, vx))

    return {
        "valid": True,
        "vx": float(vx),
        "vy": float(vy),
        "speed": float(speed),
        "angle": float(angle),
        "r2_x": float(r2_x),
        "r2_y": float(r2_y),
        "r2_avg": float((r2_x + r2_y) / 2),
        "n_points": len(positions),
        "residual_rms": float(np.sqrt((ss_res_x + ss_res_y) / (2 * len(positions)))),
    }
