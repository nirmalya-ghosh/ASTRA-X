"""
AstraX Engine — Processing Pipeline
Orchestrates calibration, noise reduction, enhancement, and registration steps.
Now expanded into an OmniPipeline to route arbitrary file types.
"""

import logging
import numpy as np
from typing import Dict, Any, List, Optional
from astrax_engine.processing import calibration, noise, enhancement, registration

logger = logging.getLogger("astrax.engine.processing.pipeline")

class OmniPipeline:
    """Universal router for different file types."""

    def __init__(self, file_type: str, steps: List[Dict[str, Any]] = None):
        self.file_type = file_type
        self.steps = steps or []

    def process(self, data: Any, context: Dict[str, Any] = None) -> Any:
        if self.file_type == "fits":
            pipeline = ProcessingPipeline(self.steps)
            return pipeline.process_frame(data, context)
        elif self.file_type == "image":
            # Pass to Vision pipeline (to be implemented)
            from astrax_engine.processing.vision import VisionPipeline
            pipeline = VisionPipeline(self.steps)
            return pipeline.process_image(data, context)
        elif self.file_type == "data":
            # Pass to Data pipeline (to be implemented)
            from astrax_engine.processing.data import DataPipeline
            pipeline = DataPipeline(self.steps)
            return pipeline.process_dataset(data, context)
        else:
            logger.warning(f"Unsupported file type for processing: {self.file_type}")
            return data

class ProcessingPipeline:
    """Configurable image processing pipeline (Legacy Astro)."""

    def __init__(self, steps: List[Dict[str, Any]] = None):
        self.steps = steps or []

    def process_frame(self, data: np.ndarray, context: Dict[str, Any] = None) -> np.ndarray:
        result = data.copy()
        context = context or {}

        for step in self.steps:
            if not step.get("enabled", True):
                continue
            
            name = step["name"]
            params = step.get("params", {})
            
            try:
                if name == "apply_flat_field":
                    flat = context.get("flat_frame")
                    if flat is not None: result = calibration.apply_flat_field(result, flat)
                elif name == "subtract_dark":
                    dark = context.get("dark_frame")
                    if dark is not None: result = calibration.subtract_dark(result, dark, params.get("scale", 1.0))
                elif name == "subtract_bias":
                    bias = context.get("bias_frame")
                    if bias is not None: result = calibration.subtract_bias(result, bias)
                elif name == "sigma_clip":
                    result = noise.sigma_clip_image(result, sigma=params.get("sigma", 3.0), max_iter=params.get("max_iter", 5))
                elif name == "clahe_enhance":
                    result = enhancement.clahe_enhance(result, clip_limit=params.get("clip_limit", 3.0), tile_size=params.get("tile_size", 8))
                elif name == "contrast_stretch":
                    result = enhancement.contrast_stretch(result, low_pct=params.get("low_pct", 1.0), high_pct=params.get("high_pct", 99.0))
                elif name == "normalize_zscale":
                    result = enhancement.normalize_zscale(result)
                elif name == "align_images":
                    ref = context.get("reference_frame")
                    if ref is not None: result, _ = registration.align_images(ref, result, method=params.get("method", "astroalign"))
            except Exception as e:
                logger.error(f"Error in pipeline step {name}: {e}")
                
        return result
