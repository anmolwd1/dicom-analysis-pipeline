from dicom_pipeline import inventory


def test_build_inventory_df_shape_and_columns(read_results):
    df = inventory.build_inventory_df(read_results)
    assert len(df) == len(read_results)
    for col in ["PatientID", "Modality", "StudyInstanceUID", "FileSizeKB", "TransferSyntaxUID"]:
        assert col in df.columns


def test_build_inventory_df_handles_missing_transfer_syntax(read_results):
    # Some bundled sample files have a file_meta with no TransferSyntaxUID set --
    # this must not raise and must record None rather than the string "None".
    df = inventory.build_inventory_df(read_results)
    assert not (df["TransferSyntaxUID"] == "None").any()


def test_unreadable_file_becomes_parse_error_row():
    row = inventory.build_inventory_row("bad.dcm", None, "unreadable: boom")
    assert row == {"filepath": "bad.dcm", "parse_error": "unreadable: boom"}
