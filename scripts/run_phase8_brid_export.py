from __future__ import annotations

import argparse
from pathlib import Path

from devoteam_reference_ai.phase8_brid_export import (
    build_pre_pdf_outputs,
    finalize_run,
    load_phase8_config,
    verify_run,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build or verify the audited synthetic BRID Phase 8 export."
    )
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--audit-workbook", type=Path, required=True)
    parser.add_argument("--reference-template", type=Path, required=True)
    parser.add_argument("--approval", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--mode",
        choices=("build-docx", "finalize", "verify"),
        default="build-docx",
    )
    parser.add_argument(
        "--visual-qa-status",
        choices=("PASSED", "FAILED", "PENDING"),
        default="PENDING",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.mode == "build-docx":
        config, data, template = build_pre_pdf_outputs(
            audit_workbook=args.audit_workbook,
            reference_template=args.reference_template,
            approval_path=args.approval,
            config_path=args.config,
            output_dir=args.output_dir,
        )
        output = load_phase8_config(args.config)["output"]
        print(args.output_dir / output["docx_name"])
        print(
            f"records={data['metrics']['selected_references']} "
            f"eligibility={data['metrics']['eligibility_passed']}/"
            f"{data['metrics']['eligibility_total']} "
            f"must={data['metrics']['must_covered']}/{data['metrics']['must_total']} "
            f"template={template['sha256']}"
        )
        return
    if args.mode == "finalize":
        manifest = finalize_run(
            config_path=args.config,
            audit_workbook=args.audit_workbook,
            reference_template=args.reference_template,
            output_dir=args.output_dir,
            visual_qa_status=args.visual_qa_status,
        )
        print(manifest["status"])
        return
    result = verify_run(output_dir=args.output_dir, config_path=args.config)
    print(result["manifest"]["status"])


if __name__ == "__main__":
    main()
