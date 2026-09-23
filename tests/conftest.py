import shutil
import warnings
from pathlib import Path

import pytest

warnings.filterwarnings("ignore", category=UserWarning, module="pydicom")


@pytest.fixture(scope="session")
def sample_dicom_dir(tmp_path_factory):
    """A folder of pydicom's bundled public sample DICOM files."""
    from pydicom.data import get_testdata_files

    inbox = tmp_path_factory.mktemp("dicom_inbox")
    for src in get_testdata_files("*.dcm"):
        shutil.copy(src, inbox / Path(src).name)
    return inbox


@pytest.fixture(scope="session")
def read_results(sample_dicom_dir):
    from dicom_pipeline import ingest

    return ingest.read_all(sample_dicom_dir)


@pytest.fixture(scope="session")
def ct_dataset():
    """A single clean, known-good CT dataset for pixel/processing tests."""
    import pydicom
    from pydicom.data import get_testdata_file

    return pydicom.dcmread(get_testdata_file("CT_small.dcm"))
