"""
AstraX Engine — Visualization Renderer
Fast 2D rendering of FITS data for web preview.
"""

import logging
import numpy as np
import io
import base64

logger = logging.getLogger("astrax.engine.visualization.renderer")


def render_preview(
    data: np.ndarray,
    stretch: str = "zscale",
    colormap: str = "gray",
    size: tuple[int, int] = None,
    output_format: str = "png"
) -> bytes:
    """Render 2D numpy array to an image byte string."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        
        # Avoid modifying original data
        img_data = data.copy()
        
        # Subsample if size provided
        if size is not None:
            from skimage.transform import resize
            img_data = resize(img_data, size, anti_aliasing=True)
            
        # Apply stretch
        if stretch == "zscale":
            from astropy.visualization import ZScaleInterval
            interval = ZScaleInterval()
            vmin, vmax = interval.get_limits(img_data)
        elif stretch == "minmax":
            vmin, vmax = np.nanmin(img_data), np.nanmax(img_data)
        elif stretch == "asinh":
            from astropy.visualization import AsinhStretch
            from astropy.visualization import MinMaxInterval
            interval = MinMaxInterval()
            vmin, vmax = interval.get_limits(img_data)
            img_data = AsinhStretch()( (img_data - vmin) / (vmax - vmin + 1e-10) )
            vmin, vmax = 0, 1
        else:
            vmin, vmax = np.percentile(img_data, [1.0, 99.0])
            
        # Render using matplotlib
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.axis('off')
        fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
        
        ax.imshow(
            img_data, 
            cmap=colormap, 
            vmin=vmin, 
            vmax=vmax, 
            origin='lower',
            interpolation='nearest'
        )
        
        buf = io.BytesIO()
        plt.savefig(buf, format=output_format, pad_inches=0, bbox_inches='tight', dpi=100)
        plt.close(fig)
        
        buf.seek(0)
        return buf.read()
        
    except Exception as e:
        logger.error(f"Failed to render preview: {e}")
        # Return empty 1x1 png as fallback
        return b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDAT\x08\xd7c\x00\x00\x00\x02\x00\x01\xe5\x27\xde\xfc\x00\x00\x00\x00IEND\xaeB`\x82'


def render_preview_base64(data: np.ndarray, **kwargs) -> str:
    """Render to base64 string for direct frontend embedding."""
    img_bytes = render_preview(data, **kwargs)
    return base64.b64encode(img_bytes).decode('utf-8')
