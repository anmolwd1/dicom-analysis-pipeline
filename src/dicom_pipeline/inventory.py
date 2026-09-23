"""Structured metadata inventory over a batch of parsed DICOM datasets."""

from __future__ import annotations

import os

import pandas as pd
from pydicom.dataset import FileDataset


def _tag(ds: FileDataset, keyword: str, default=None):
    return getattr(ds, keyword, default)


def _transfer_syntax(ds: FileDataset) -> str | None:
    file_meta = getattr(ds, "file_meta", None)
    if file_meta is None:
        return None
    ts = getattr(file_meta, "TransferSyntaxUID", None)
    return str(ts) if ts is not None else None


def build_inventory_row(path: str, ds: FileDataset | None, warning: str | None) -> dict:
    """Extract the tags an operations/QA dashboard would want from one instance."""
    if ds is None:
        return {"filepath": path, "parse_error": warning}

    return {
        "filepath": path,
        "parse_error": warning,
        "PatientID": _tag(ds, "PatientID"),
        "PatientName": str(_tag(ds, "PatientName")) if _tag(ds, "PatientName") else None,
        "PatientBirthDate": _tag(ds, "PatientBirthDate"),
        "PatientSex": _tag(ds, "PatientSex"),
        "StudyInstanceUID": _tag(ds, "StudyInstanceUID"),
        "SeriesInstanceUID": _tag(ds, "SeriesInstanceUID"),
        "SOPInstanceUID": _tag(ds, "SOPInstanceUID"),
        "StudyDate": _tag(ds, "StudyDate"),
        "StudyDescription": _tag(ds, "StudyDescription"),
        "SeriesDescription": _tag(ds, "SeriesDescription"),
        "Modality": _tag(ds, "Modality"),
        "Manufacturer": _tag(ds, "Manufacturer"),
        "ManufacturerModelName": _tag(ds, "ManufacturerModelName"),
        "InstitutionName": _tag(ds, "InstitutionName"),
        "Rows": _tag(ds, "Rows"),
        "Columns": _tag(ds, "Columns"),
        "BitsAllocated": _tag(ds, "BitsAllocated"),
        "PixelSpacing": str(_tag(ds, "PixelSpacing")) if _tag(ds, "PixelSpacing") else None,
        "SliceThickness": _tag(ds, "SliceThickness"),
        "TransferSyntaxUID": _transfer_syntax(ds),
        "HasPixelData": "PixelData" in ds,
        "FileSizeKB": round(os.path.getsize(path) / 1024, 1),
    }


def build_inventory_df(read_results: dict[str, tuple[FileDataset | None, str | None]]) -> pd.DataFrame:
    """Build the full metadata inventory DataFrame from :func:`ingest.read_all` output."""
    rows = [build_inventory_row(f, ds, warning) for f, (ds, warning) in read_results.items()]
    return pd.DataFrame(rows)
