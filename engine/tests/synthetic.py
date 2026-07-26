import numpy as np


def gaussian_star_field(
    shape=(96, 96),
    stars=None,
    background=100.0,
    noise=0.0,
    seed=42,
):
    """Create a small synthetic image with Gaussian point sources."""
    rng = np.random.default_rng(seed)
    image = np.full(shape, background, dtype=np.float32)
    yy, xx = np.indices(shape, dtype=np.float32)

    for x, y, flux, sigma in stars or []:
        image += flux * np.exp(-0.5 * (((xx - x) / sigma) ** 2 + ((yy - y) / sigma) ** 2))

    if noise > 0:
        image += rng.normal(0, noise, shape).astype(np.float32)
    return image
