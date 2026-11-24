"""Resample a breast plate after illustrative displacement under the probe face."""

import numpy as np

# Keep this matched to the scan-plane displacement in scene.js.
SETTLE_DEPTH_MM = 30.0


def compress_plates(gray, section, depths_mm, field, *, compression_mm, depth_mm):
    """Shift the probe and contract shallow tissue without changing pixel pitch."""
    if not np.isfinite(compression_mm) or not 0 < compression_mm < min(depth_mm, 2 * SETTLE_DEPTH_MM / 3):
        raise ValueError('Compression must preserve an ordered depth field.')

    pitch = depths_mm[1] - depths_mm[0]
    compressed_depth = depth_mm - compression_mm
    active = (depths_mm >= 0) & (depths_mm <= compressed_depth)
    # The original tissue depth maps to depth - compression * smoothstep(depth / settle).
    # Invert that monotone mapping for each active output row.
    display = depths_mm[active]
    low = display.copy()
    high = display + compression_mm
    for _ in range(20):
        middle = (low + high) / 2
        fraction = np.minimum(middle / SETTLE_DEPTH_MM, 1)
        mapped = middle - compression_mm * fraction**2 * (3 - 2 * fraction)
        below = mapped < display
        low = np.where(below, middle, low)
        high = np.where(below, high, middle)

    raster_row = ((low + high) / 2 - depths_mm[0]) / pitch
    raster_row = np.clip(raster_row, 0, len(depths_mm) - 1)
    before = raster_row.astype(np.intp)
    after = np.minimum(before + 1, len(depths_mm) - 1)
    mix = raster_row - before

    def resample(image):
        result = np.zeros_like(image)
        weight = mix.reshape((-1,) + (1,) * (image.ndim - 1))
        result[active] = np.rint(image[before] * (1 - weight) + image[after] * weight).astype(image.dtype)
        result[~field] = 0
        return result

    return resample(gray), resample(section)
