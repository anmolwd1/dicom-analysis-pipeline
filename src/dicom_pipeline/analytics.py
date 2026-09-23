"""Aggregate summary statistics over an ingested batch."""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd


def build_summary(inventory_df: pd.DataFrame, qc_df: pd.DataFrame) -> dict:
    """Roll up the inventory and QC report into a single JSON-serializable summary."""
    status_counts = qc_df["status"].value_counts()
    return {
        "total_files_ingested": int(len(inventory_df)),
        "unique_patients": int(inventory_df["PatientID"].nunique(dropna=True)),
        "unique_studies": int(inventory_df["StudyInstanceUID"].nunique(dropna=True)),
        "modalities_seen": sorted(inventory_df["Modality"].dropna().unique().tolist()),
        "qc_pass": int(status_counts.get("PASS", 0)),
        "qc_warn": int(status_counts.get("WARN", 0)),
        "qc_fail": int(status_counts.get("FAIL", 0)),
        "total_size_mb": round(float(inventory_df["FileSizeKB"].sum()) / 1024, 2),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
