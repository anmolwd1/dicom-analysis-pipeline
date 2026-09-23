"""Command-line entry point: run the full pipeline over a folder of DICOM files.

    dicom-pipeline run --input INBOX --output OUTDIR
    dicom-pipeline run --sample --output OUTDIR   # zero-setup demo using pydicom's bundled files
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from . import ingest, inventory, qc, deidentify, analytics


def _stage_sample_data(inbox: Path) -> None:
    from pydicom.data import get_testdata_files

    inbox.mkdir(parents=True, exist_ok=True)
    for src in get_testdata_files("*.dcm"):
        dst = inbox / Path(src).name
        if not dst.exists():
            shutil.copy(src, dst)


def run(input_dir: str | None, output_dir: str, use_sample: bool, deidentify_output: bool) -> dict:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    if use_sample:
        inbox = out / "inbox"
        _stage_sample_data(inbox)
        input_dir = str(inbox)
    elif not input_dir:
        raise SystemExit("Provide --input <folder> or use --sample for the bundled demo data.")

    print(f"Reading DICOM files from {input_dir} ...")
    read_results = ingest.read_all(input_dir)
    print(f"Parsed {len(read_results)} files.")

    inventory_df = inventory.build_inventory_df(read_results)
    inventory_csv = out / "dicom_inventory.csv"
    inventory_df.to_csv(inventory_csv, index=False)
    print(f"Wrote inventory -> {inventory_csv}")

    qc_df = qc.build_qc_df(read_results)
    qc_csv = out / "dicom_qc_report.csv"
    qc_df.drop(columns=["issues"]).to_csv(qc_csv, index=False)
    print(f"Wrote QC report -> {qc_csv}  ({dict(qc_df['status'].value_counts())})")

    if deidentify_output:
        deid_dir = out / "deidentified"
        deid_dir.mkdir(exist_ok=True)
        count, failures = 0, []
        for f, (ds, _warning) in read_results.items():
            if ds is None:
                continue
            deid = deidentify.deidentify(ds)
            try:
                deid.save_as(deid_dir / Path(f).name, write_like_original=True)
                count += 1
            except Exception as e:
                failures.append((Path(f).name, str(e)))
        print(f"De-identified {count} files -> {deid_dir}" + (f" ({len(failures)} skipped)" if failures else ""))

    summary = analytics.build_summary(inventory_df, qc_df)
    summary_path = out / "pipeline_summary_report.json"
    summary_path.write_text(json.dumps(summary, indent=2))
    print(f"Wrote summary -> {summary_path}")
    print(json.dumps(summary, indent=2))

    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dicom-pipeline", description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run the full pipeline over a folder of DICOM files.")
    run_parser.add_argument("--input", help="Folder containing .dcm files.")
    run_parser.add_argument("--output", default="./output", help="Folder to write reports/artifacts to.")
    run_parser.add_argument(
        "--sample", action="store_true",
        help="Use pydicom's bundled public sample files instead of --input (zero-setup demo).",
    )
    run_parser.add_argument(
        "--no-deidentify", action="store_true",
        help="Skip writing de-identified copies (faster on large batches).",
    )

    args = parser.parse_args(argv)

    if args.command == "run":
        run(args.input, args.output, args.sample, deidentify_output=not args.no_deidentify)
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
