"""
AstraX AI — Source Deblending for Astronomical Images

Inspired by astro_rcnn's deblending approach (Burke et al. 2019).
Uses watershed segmentation with multi-threshold peak detection to
separate overlapping astronomical sources.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class DeblendedSource:
    """A single deblended component."""
    component_id: int
    parent_label: int
    x_centroid: float
    y_centroid: float
    flux: float
    peak_value: float
    area_pixels: int
    confidence: float


@dataclass
class DeblendResult:
    """Result of a deblending run."""
    components: list[DeblendedSource] = field(default_factory=list)
    n_blended_groups: int = 0
    n_total_components: int = 0


def run_deblending(
    image_data: np.ndarray,
    label_map: Optional[np.ndarray] = None,
    min_area: int = 5,
    contrast: float = 0.001,
) -> DeblendResult:
    """
    Deblend overlapping sources using multi-threshold watershed.

    Parameters
    ----------
    image_data : 2D array
    label_map : pre-existing segmentation labels (optional)
    min_area : minimum pixel area for a component
    contrast : minimum contrast between peaks to separate

    Returns
    -------
    DeblendResult
    """
    from scipy import ndimage
    from skimage.segmentation import watershed
    from skimage.feature import peak_local_max
    from skimage.measure import label, regionprops

    data = image_data.astype(np.float64)

    if label_map is None:
        bg = np.median(data)
        std = np.std(data)
        mask = data > (bg + 3 * std)
        label_map, _ = ndimage.label(mask)

    unique_labels = np.unique(label_map)
    unique_labels = unique_labels[unique_labels > 0]

    components: list[DeblendedSource] = []
    n_blended = 0
    comp_id = 0

    for lbl in unique_labels:
        region_mask = label_map == lbl
        region_data = data * region_mask
        region_max = region_data.max()
        if region_max <= 0:
            continue

        min_distance = max(2, int(np.sqrt(region_mask.sum() / np.pi) * 0.3))
        try:
            coords = peak_local_max(
                region_data, min_distance=min_distance,
                threshold_abs=region_max * contrast, num_peaks=20,
            )
        except Exception:
            coords = np.array([])

        if len(coords) <= 1:
            props = regionprops(region_mask.astype(int), intensity_image=data)
            if props:
                p = props[0]
                comp_id += 1
                components.append(DeblendedSource(
                    component_id=comp_id, parent_label=int(lbl),
                    x_centroid=float(p.centroid[1]), y_centroid=float(p.centroid[0]),
                    flux=float(p.intensity_mean * p.area),
                    peak_value=float(region_data.max()),
                    area_pixels=int(p.area), confidence=1.0,
                ))
            continue

        n_blended += 1
        markers = np.zeros_like(data, dtype=int)
        for i, (y, x) in enumerate(coords):
            markers[y, x] = i + 1

        ws_labels = watershed(-region_data, markers, mask=region_mask)

        for ws_lbl in np.unique(ws_labels):
            if ws_lbl == 0:
                continue
            comp_mask = ws_labels == ws_lbl
            comp_area = comp_mask.sum()
            if comp_area < min_area:
                continue
            comp_data = data * comp_mask
            comp_flux = comp_data.sum()
            total_flux = (data * region_mask).sum()
            confidence = comp_flux / total_flux if total_flux > 0 else 0.5

            yy, xx = np.where(comp_mask)
            weights = comp_data[comp_mask]
            w_sum = weights.sum()
            if w_sum > 0:
                cx = float(np.average(xx, weights=weights))
                cy = float(np.average(yy, weights=weights))
            else:
                cx, cy = float(xx.mean()), float(yy.mean())

            comp_id += 1
            components.append(DeblendedSource(
                component_id=comp_id, parent_label=int(lbl),
                x_centroid=cx, y_centroid=cy,
                flux=round(float(comp_flux), 2),
                peak_value=round(float(comp_data.max()), 2),
                area_pixels=int(comp_area),
                confidence=round(float(confidence), 3),
            ))

    logger.info("Deblending: %d components, %d blended groups", len(components), n_blended)
    return DeblendResult(components=components, n_blended_groups=n_blended, n_total_components=len(components))
