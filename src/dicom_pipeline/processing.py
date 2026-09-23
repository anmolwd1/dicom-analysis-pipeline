"""Pixel data decoding, windowing, and basic image processing."""

from __future__ import annotations

import numpy as np
import pydicom
from pydicom.dataset import FileDataset
from pydicom.pixels import apply_color_lut

COLOR_PHOTOMETRIC_INTERPRETATIONS = {
    "RGB", "YBR_FULL", "YBR_FULL_422", "YBR_RCT", "YBR_ICT", "PALETTE COLOR",
}


def get_display_array(ds: FileDataset) -> tuple[np.ndarray, bool]:
    """Return ``(array, is_color)`` normalized to ``[0, 1]`` and ready for
    ``imshow``, correctly handling grayscale windowing, color photometric
    interpretations, and inverted (``MONOCHROME1``) display."""
    arr = ds.pixel_array
    photometric = getattr(ds, "PhotometricInterpretation", "MONOCHROME2")

    if arr.ndim >= 3 and arr.shape[0] > 1 and photometric not in ("RGB",):
        arr = arr[0]  # multi-frame: show the first frame

    if photometric in COLOR_PHOTOMETRIC_INTERPRETATIONS:
        if photometric == "PALETTE COLOR":
            arr = apply_color_lut(arr, ds)
        arr = arr.astype(np.float64)
        lo, hi = arr.min(), arr.max()
        arr = (arr - lo) / (hi - lo) if hi > lo else np.zeros_like(arr)
        return arr, True

    arr = arr.astype(np.float64)
    slope = float(getattr(ds, "RescaleSlope", 1))
    intercept = float(getattr(ds, "RescaleIntercept", 0))
    arr = arr * slope + intercept

    wc = getattr(ds, "WindowCenter", None)
    ww = getattr(ds, "WindowWidth", None)
    if wc is not None and ww is not None:
        wc = float(wc[0] if isinstance(wc, pydicom.multival.MultiValue) else wc)
        ww = float(ww[0] if isinstance(ww, pydicom.multival.MultiValue) else ww)
        lo, hi = wc - ww / 2, wc + ww / 2
    else:
        lo, hi = np.percentile(arr, [1, 99])

    arr = np.clip(arr, lo, hi)
    arr = (arr - lo) / (hi - lo) if hi > lo else np.zeros_like(arr)

    # MONOCHROME1 encodes 0 = white / max = black -- the opposite of the usual
    # radiological display convention -- so invert it to render correctly.
    if photometric == "MONOCHROME1":
        arr = 1.0 - arr

    return arr, False


def clahe_enhance(array: np.ndarray, clip_limit: float = 0.02) -> np.ndarray:
    """Contrast-limited adaptive histogram equalization on a normalized
    grayscale array (values in ``[0, 1]``)."""
    from skimage import exposure

    return exposure.equalize_adapthist(array, clip_limit=clip_limit)
