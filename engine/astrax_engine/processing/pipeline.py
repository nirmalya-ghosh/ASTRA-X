"""
AstraX Engine — Processing Pipeline
Orchestrates calibration, noise reduction, enhancement, and registration steps.
"""

import logging
import numpy as np
from typing import Dict, Any, List, Optional
from astrax_engine.processing import calibration, noise, enhancement, registration

logger = logging.getLogger("astrax.engine.processing.pipeline")


class ProcessingPipeline:
    """Configurable image processing pipeline."""

    def __init__(self, steps: List[Dict[str, Any]] = None):
        """
        Initialize pipeline with a list of steps.
        Each step should be a dict with 'name', 'enabled', and 'params'.
        """
        self.steps = steps or []

    def process_frame(self, data: np.ndarray, context: Dict[str, Any] = None) -> np.ndarray:
        """Run the processing pipeline on a single frame."""
        result = data.copy()
        context = context or {}

        for step in self.steps:
            if not step.get("enabled", True):
                continue
            
            name = step["name"]
            params = step.get("params", {})
            logger.debug(f"Running pipeline step: {name}")

            try:
                if name == "apply_flat_field":
                    flat = context.get("flat_frame")
                    if flat is not None:
                        result = calibration.apply_flat_field(result, flat)
                elif name == "subtract_dark":
                    dark = context.get("dark_frame")
                    if dark is not None:
                        scale = params.get("scale", 1.0)
                        result = calibration.subtract_dark(result, dark, scale)
                elif name == "subtract_bias":
                    bias = context.get("bias_frame")
                    if bias is not None:
                        result = calibration.subtract_bias(result, bias)
                elif name == "apply_bad_pixel_mask":
                    result = calibration.apply_bad_pixel_mask(
                        result, 
                        mask=context.get("bad_pixel_mask"),
                        hot_threshold=params.get("hot_threshold", 50.0),
                        dead_threshold=params.get("dead_threshold", -10.0)
                    )
                elif name == "sigma_clip":
                    result = noise.sigma_clip_image(
                        result, 
                        sigma=params.get("sigma", 3.0),
                        max_iter=params.get("max_iter", 5)
                    )
                elif name == "median_filter":
                    result = noise.median_filter_image(result, size=params.get("size", 3))
                elif name == "gaussian_filter":
                    result = noise.gaussian_filter_image(result, sigma=params.get("sigma", 1.0))
                elif name == "remove_cosmic_rays":
                    result, _ = noise.remove_cosmic_rays(
                        result,
                        gain=params.get("gain", 1.0),
                        readnoise=params.get("readnoise", 5.0),
                        sigclip=params.get("sigclip", 4.5)
                    )
                elif name == "clahe_enhance":
                    result = enhancement.clahe_enhance(
                        result,
                        clip_limit=params.get("clip_limit", 3.0),
                        tile_size=params.get("tile_size", 8)
                    )
                elif name == "contrast_stretch":
                    result = enhancement.contrast_stretch(
                        result,
                        low_pct=params.get("low_pct", 1.0),
                        high_pct=params.get("high_pct", 99.0)
                    )
                elif name == "normalize_zscale":
                    result = enhancement.normalize_zscale(result)
                elif name == "normalize_asinh":
                    result = enhancement.normalize_asinh(result, a=params.get("a", 0.1))
                elif name == "normalize_minmax":
                    result = enhancement.normalize_minmax(result)
                elif name == "align_images":
                    ref = context.get("reference_frame")
                    if ref is not None:
                        result, _ = registration.align_images(ref, result, method=params.get("method", "astroalign"))
                else:
                    logger.warning(f"Unknown pipeline step: {name}")
            except Exception as e:
                logger.error(f"Error in pipeline step {name}: {e}")
                
        return result
