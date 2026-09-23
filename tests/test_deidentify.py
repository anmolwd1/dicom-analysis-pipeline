from dicom_pipeline import deidentify


def test_deidentify_scrubs_phi_tags(ct_dataset):
    salt = b"test-salt"
    deid = deidentify.deidentify(ct_dataset, salt=salt)

    assert deid.PatientName == ""
    assert str(deid.PatientID).startswith("ANON-")
    assert deid.PatientIdentityRemoved == "YES"
    assert "DeidentificationMethod" in deid


def test_deidentify_does_not_mutate_original(ct_dataset):
    original_id = ct_dataset.PatientID
    deidentify.deidentify(ct_dataset, salt=b"test-salt")
    assert ct_dataset.PatientID == original_id


def test_pseudonymize_is_deterministic_and_not_reversible():
    salt = b"fixed-salt"
    a = deidentify.pseudonymize("PATIENT-123", salt)
    b = deidentify.pseudonymize("PATIENT-123", salt)
    c = deidentify.pseudonymize("PATIENT-456", salt)

    assert a == b
    assert a != c
    assert "PATIENT-123" not in a
