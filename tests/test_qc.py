import copy

from dicom_pipeline import qc


def test_clean_ct_file_passes(ct_dataset):
    result = qc.qc_check("CT_small.dcm", ct_dataset, None)
    assert result["status"] == "PASS"
    assert result["issues"] == []


def test_unreadable_file_is_hard_fail():
    result = qc.qc_check("bad.dcm", None, "unreadable: boom")
    assert result["status"] == "FAIL"


def test_missing_required_tag_is_hard_fail(ct_dataset):
    # Dataset.copy() is a shallow copy that shares storage with the original --
    # mutating it would corrupt the shared, session-scoped ct_dataset fixture
    # for every other test. Use a real deepcopy to isolate this mutation.
    ds = copy.deepcopy(ct_dataset)
    del ds.PatientID
    result = qc.qc_check("f.dcm", ds, None)
    assert result["status"] == "FAIL"
    assert any(i.startswith("missing_required_tag:PatientID") for i in result["issues"])


def test_non_image_object_without_pixel_data_is_warn_not_fail(ct_dataset):
    ds = copy.deepcopy(ct_dataset)
    del ds.PixelData
    result = qc.qc_check("f.dcm", ds, None)
    assert result["status"] == "WARN"
    assert "no_pixel_data" in result["issues"]


def test_garbage_parsed_file_is_flagged_by_qc(tmp_path):
    from dicom_pipeline import ingest

    bad_file = tmp_path / "not_a_dicom.dcm"
    bad_file.write_bytes(b"this is not a dicom file" * 20)
    ds, warning = ingest.read_all(tmp_path)[str(bad_file)]

    result = qc.qc_check(str(bad_file), ds, warning)
    assert result["status"] == "FAIL"


def test_build_qc_df_status_counts_cover_all_rows(read_results):
    df = qc.build_qc_df(read_results)
    assert len(df) == len(read_results)
    assert set(df["status"].unique()) <= {"PASS", "WARN", "FAIL"}
