"""Demonstration de-identification, loosely modelled on DICOM PS3.15.

Not a certified de-identification tool. A production deployment should use a
validated product (RSNA CTP, Orthanc's anonymization plugin, or the
`dicom-anonymizer` library) with its tag list reviewed against the
institution's own PHI policy and HIPAA Safe Harbor / Expert Determination
requirements.
"""

from __future__ import annotations

import copy
import hashlib
import os

from pydicom.dataset import FileDataset

PHI_TAGS_TO_PSEUDONYMIZE = ["PatientID"]
PHI_TAGS_TO_BLANK = [
    "PatientName", "PatientBirthDate", "PatientAddress", "OtherPatientIDs",
    "OtherPatientNames", "InstitutionName", "InstitutionAddress",
    "ReferringPhysicianName", "PerformingPhysicianName", "OperatorsName",
    "StationName", "RequestingPhysician", "PhysiciansOfRecord",
]


def pseudonymize(value: str, salt: bytes) -> str:
    """Deterministic pseudonym: same input + salt always maps to the same output,
    without being reversible."""
    digest = hashlib.sha256(salt + str(value).encode("utf-8")).hexdigest()[:12]
    return f"ANON-{digest}"


def get_salt() -> bytes:
    """Read the pseudonymization salt from ``DICOM_PIPELINE_SALT``, or fall back
    to a fixed demo value. Set the env var in any real deployment."""
    return os.environ.get("DICOM_PIPELINE_SALT", "demo-salt-change-me-per-deployment").encode("utf-8")


def deidentify(ds: FileDataset, salt: bytes | None = None) -> FileDataset:
    """Return a de-identified copy of ``ds``. Does not modify ``ds`` in place."""
    salt = salt if salt is not None else get_salt()
    # Dataset.copy() is a shallow copy that shares underlying element storage
    # with the original -- mutating the "copy" silently mutates the input too.
    # A real deepcopy is required to actually isolate the de-identified output.
    out = copy.deepcopy(ds)

    for t in PHI_TAGS_TO_PSEUDONYMIZE:
        if hasattr(out, t):
            setattr(out, t, pseudonymize(getattr(out, t), salt))

    for t in PHI_TAGS_TO_BLANK:
        if hasattr(out, t):
            setattr(out, t, "")

    # Strip vendor/private tags, which can carry embedded PHI (e.g. burned-in overlays).
    out.remove_private_tags()

    out.PatientIdentityRemoved = "YES"
    out.DeidentificationMethod = "dicom_pipeline: basic tag blanking + pseudonymized PatientID"

    return out
