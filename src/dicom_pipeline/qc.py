"""Data-quality / DICOM-conformance checks for an ingested batch."""

from __future__ import annotations

import pandas as pd
from pydicom.dataset import FileDataset

REQUIRED_TAGS = [
    "PatientID", "StudyInstanceUID", "SeriesInstanceUID", "SOPInstanceUID", "Modality",
]

SUPPORTED_TRANSFER_SYNTAXES = {
    "1.2.840.10008.1.2",       # Implicit VR Little Endian
    "1.2.840.10008.1.2.1",     # Explicit VR Little Endian
    "1.2.840.10008.1.2.4.50",  # JPEG Baseline
    "1.2.840.10008.1.2.4.70",  # JPEG Lossless
    "1.2.840.10008.1.2.4.90",  # JPEG 2000 Lossless
    "1.2.840.10008.1.2.4.91",  # JPEG 2000
}

# Only these conditions make an instance unusable. Everything else (e.g. a
# non-image SOP class with no pixel data, or a transfer syntax this basic
# pipeline doesn't decode) is worth a human glance but isn't a rejection.
_HARD_FAIL_PREFIXES = ("unreadable", "missing_required_tag", "pixel_data_decode_error")


def qc_check(path: str, ds: FileDataset | None, warning: str | None) -> dict:
    """Run conformance checks on one instance and return an issue report."""
    issues: list[str] = []

    if ds is None:
        return {"filepath": path, "issues": [warning or "unreadable"], "issue_count": 1, "status": "FAIL"}

    if warning:
        issues.append(warning)

    for req in REQUIRED_TAGS:
        if not getattr(ds, req, None):
            issues.append(f"missing_required_tag:{req}")

    file_meta = getattr(ds, "file_meta", None)
    ts_raw = getattr(file_meta, "TransferSyntaxUID", None) if file_meta is not None else None
    if ts_raw is None:
        issues.append("missing_transfer_syntax")
    elif str(ts_raw) not in SUPPORTED_TRANSFER_SYNTAXES:
        issues.append(f"unsupported_transfer_syntax:{ts_raw}")

    if "PixelData" in ds:
        try:
            _ = ds.pixel_array
        except Exception as e:
            issues.append(f"pixel_data_decode_error:{type(e).__name__}")
    else:
        # Expected for non-image SOP classes (structured reports, RT structure
        # sets, key object selections) -- absence alone isn't a defect.
        issues.append("no_pixel_data")

    if not issues:
        status = "PASS"
    elif any(i.startswith(_HARD_FAIL_PREFIXES) for i in issues):
        status = "FAIL"
    else:
        status = "WARN"

    return {"filepath": path, "issues": issues, "issue_count": len(issues), "status": status}


def build_qc_df(read_results: dict[str, tuple[FileDataset | None, str | None]]) -> pd.DataFrame:
    """Run :func:`qc_check` over a whole batch and return the report as a DataFrame."""
    rows = [qc_check(f, ds, warning) for f, (ds, warning) in read_results.items()]
    df = pd.DataFrame(rows)
    df["issues_str"] = df["issues"].apply(lambda x: "; ".join(x) if x else "")
    return df
