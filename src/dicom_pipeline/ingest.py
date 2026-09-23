"""Safe DICOM file discovery and parsing."""

from __future__ import annotations

import glob
import os
from pathlib import Path
from typing import Iterator

import pydicom
from pydicom.dataset import FileDataset
from pydicom.errors import InvalidDicomError


def iter_dicom_paths(folder: str | os.PathLike) -> Iterator[str]:
    """Yield every ``.dcm`` file path under ``folder`` (non-recursive)."""
    yield from sorted(glob.glob(str(Path(folder) / "*.dcm")))


def safe_read_dicom(path: str | os.PathLike) -> tuple[FileDataset | None, str | None]:
    """Read a DICOM file, tolerating files without a valid preamble/meta header.

    Returns ``(dataset, warning)``. ``dataset`` is ``None`` if the file could
    not be parsed at all; ``warning`` is set when the file was readable only
    via a fallback path (e.g. a missing 128-byte preamble).
    """
    try:
        return pydicom.dcmread(path, force=False), None
    except InvalidDicomError:
        try:
            return pydicom.dcmread(path, force=True), "no_preamble_forced_read"
        except Exception as e:
            return None, f"unreadable: {e}"
    except Exception as e:
        return None, f"unreadable: {e}"


def read_all(folder: str | os.PathLike) -> dict[str, tuple[FileDataset | None, str | None]]:
    """Read every ``.dcm`` file in ``folder`` into ``{path: (dataset, warning)}``."""
    return {path: safe_read_dicom(path) for path in iter_dicom_paths(folder)}
