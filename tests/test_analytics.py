import json

from dicom_pipeline import analytics, inventory, qc


def test_build_summary_matches_inputs(read_results):
    inventory_df = inventory.build_inventory_df(read_results)
    qc_df = qc.build_qc_df(read_results)

    summary = analytics.build_summary(inventory_df, qc_df)

    assert summary["total_files_ingested"] == len(read_results)
    assert summary["qc_pass"] + summary["qc_warn"] + summary["qc_fail"] == len(read_results)
    assert "CT" in summary["modalities_seen"]


def test_build_summary_is_json_serializable(read_results):
    inventory_df = inventory.build_inventory_df(read_results)
    qc_df = qc.build_qc_df(read_results)
    summary = analytics.build_summary(inventory_df, qc_df)

    json.dumps(summary)  # must not raise
