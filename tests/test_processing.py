import numpy as np
import pydicom
from pydicom.data import get_testdata_file

from dicom_pipeline import processing


def test_get_display_array_grayscale_ct(ct_dataset):
    arr, is_color = processing.get_display_array(ct_dataset)
    assert is_color is False
    assert arr.ndim == 2
    assert arr.min() >= 0.0 and arr.max() <= 1.0


def test_get_display_array_inverts_monochrome1():
    # RG1_UNCR.dcm is a real MONOCHROME1 (CR/X-ray) sample -- 0 should render
    # as bright after our inversion fix, not as the raw (inverted) encoding.
    ds = pydicom.dcmread(get_testdata_file("RG1_UNCR.dcm"))
    assert ds.PhotometricInterpretation == "MONOCHROME1"

    arr, is_color = processing.get_display_array(ds)
    assert is_color is False

    raw = ds.pixel_array.astype(np.float64)
    lo, hi = np.percentile(raw, [1, 99])
    raw_normalized = np.clip((raw - lo) / (hi - lo), 0, 1)

    # After correction, dark-in-raw-encoding pixels should render bright, i.e.
    # the two arrays should be (roughly) inversely correlated.
    correlation = np.corrcoef(arr.ravel(), raw_normalized.ravel())[0, 1]
    assert correlation < -0.5


def test_get_display_array_color_ultrasound():
    ds = pydicom.dcmread(get_testdata_file("examples_rgb_color.dcm"))
    arr, is_color = processing.get_display_array(ds)
    assert is_color is True
    assert arr.ndim == 3
    assert arr.shape[-1] == 3


def test_clahe_enhance_preserves_shape_and_range(ct_dataset):
    arr, _ = processing.get_display_array(ct_dataset)
    enhanced = processing.clahe_enhance(arr)
    assert enhanced.shape == arr.shape
    assert enhanced.min() >= 0.0 and enhanced.max() <= 1.0
