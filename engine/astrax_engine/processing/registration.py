"""
AstraX Engine — Image Registration
Star-based alignment and subpixel registration.
"""

import logging
import numpy as np
from typing import Optional

logger = logging.getLogger("astrax.engine.processing.registration")


def align_images(
    reference: np.ndarray,
    target: np.ndarray,
    method: str = "astroalign",
) -> tuple[np.ndarray, dict]:
    """
    Align target image to reference.

    Args:
        reference: Reference image
        target: Image to align
        method: 'astroalign' or 'cross_correlation'

    Returns:
        (aligned_image, transform_info)
    """
    if method == "astroalign":
        return _align_astroalign(reference, target)
    elif method == "cross_correlation":
        return _align_cross_correlation(reference, target)
    else:
        raise ValueError(f"Unknown alignment method: {method}")


def _align_astroalign(reference: np.ndarray, target: np.ndarray) -> tuple[np.ndarray, dict]:
    """Star-based alignment using astroalign."""
    try:
        import astroalign as aa
        aligned, footprint = aa.register(target, reference)
        transform = aa.find_transform(target, reference)

        info = {
            "method": "astroalign",
            "success": True,
            "rotation": float(np.degrees(np.arctan2(transform[0].params[1][0], transform[0].params[0][0]))),
            "translation_x": float(transform[0].params[0][2]),
            "translation_y": float(transform[0].params[1][2]),
        }
        logger.info(f"Aligned using astroalign: dx={info['translation_x']:.2f}, dy={info['translation_y']:.2f}")
        return aligned, info
    except ImportError:
        logger.warning("astroalign not installed, falling back to cross-correlation")
        return _align_cross_correlation(reference, target)
    except Exception as e:
        logger.error(f"astroalign failed: {e}, falling back to cross-correlation")
        return _align_cross_correlation(reference, target)


def _align_cross_correlation(reference: np.ndarray, target: np.ndarray) -> tuple[np.ndarray, dict]:
    """Subpixel alignment via FFT cross-correlation."""
    from scipy.ndimage import shift as ndimage_shift

    # Phase correlation
    f_ref = np.fft.fft2(reference)
    f_target = np.fft.fft2(target)

    cross_power = (f_ref * np.conj(f_target)) / (np.abs(f_ref * np.conj(f_target)) + 1e-10)
    correlation = np.abs(np.fft.ifft2(cross_power))

    # Find peak
    peak_idx = np.unravel_index(np.argmax(correlation), correlation.shape)
    dy, dx = peak_idx

    # Wrap around for negative shifts
    if dy > reference.shape[0] // 2:
        dy -= reference.shape[0]
    if dx > reference.shape[1] // 2:
        dx -= reference.shape[1]

    # Apply shift
    aligned = ndimage_shift(target, (dy, dx), order=3)

    info = {
        "method": "cross_correlation",
        "success": True,
        "translation_x": float(dx),
        "translation_y": float(dy),
        "peak_correlation": float(np.max(correlation)),
    }

    logger.info(f"Aligned using cross-correlation: dx={dx:.2f}, dy={dy:.2f}")
    return aligned, info


def align_stack(
    frames: list[np.ndarray],
    reference_index: int = 0,
    method: str = "astroalign",
) -> tuple[list[np.ndarray], list[dict]]:
    """Align a stack of frames to a reference frame."""
    reference = frames[reference_index]
    aligned_frames = []
    transform_infos = []

    for i, frame in enumerate(frames):
        if i == reference_index:
            aligned_frames.append(frame)
            transform_infos.append({"method": method, "success": True, "is_reference": True})
        else:
            try:
                aligned, info = align_images(reference, frame, method=method)
                aligned_frames.append(aligned)
                transform_infos.append(info)
            except Exception as e:
                logger.error(f"Failed to align frame {i}: {e}")
                aligned_frames.append(frame)
                transform_infos.append({"method": method, "success": False, "error": str(e)})

    n_success = sum(1 for t in transform_infos if t.get("success"))
    logger.info(f"Aligned {n_success}/{len(frames)} frames")

    return aligned_frames, transform_infos
