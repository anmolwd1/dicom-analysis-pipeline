from dicom_pipeline import ingest


def test_iter_dicom_paths_finds_files(sample_dicom_dir):
    paths = list(ingest.iter_dicom_paths(sample_dicom_dir))
    assert len(paths) > 0
    assert all(p.endswith(".dcm") for p in paths)


def test_read_all_parses_known_good_file(sample_dicom_dir):
    results = ingest.read_all(sample_dicom_dir)
    ct_small = [p for p in results if p.endswith("CT_small.dcm")]
    assert ct_small, "CT_small.dcm should be present in the sample set"
    ds, warning = results[ct_small[0]]
    assert ds is not None
    assert warning is None
    assert ds.Modality == "CT"


def test_read_all_never_raises_on_bad_input(tmp_path):
    # pydicom's force=True fallback is permissive: arbitrary bytes often parse
    # into a (nonsensical) Dataset rather than raising. The guarantee ingest
    # actually provides is that it never crashes the batch -- a garbage file
    # like this is the QC stage's job to flag (via missing required tags),
    # not ingest's.
    bad_file = tmp_path / "not_a_dicom.dcm"
    bad_file.write_bytes(b"this is not a dicom file" * 20)
    results = ingest.read_all(tmp_path)
    assert str(bad_file) in results
