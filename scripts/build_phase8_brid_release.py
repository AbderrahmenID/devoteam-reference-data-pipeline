#!/usr/bin/env python3
"""Build the deterministic Phase 8 BRID audited-export release package."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


FIXED_ZIP_TIME = (2026, 7, 25, 12, 0, 0)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    implementation = workspace / "phase8_brid_v2"
    deliverables = workspace / "outputs" / "phase8_brid_audited_export"

    source_files = [
        implementation / "approval" / "PHASE_7_BRID_SHORTLIST_APPROVAL.json",
        implementation / "config" / "phase8_brid_audited_export.yaml",
        implementation / "docs" / "PHASE_8_BRID_RUNBOOK.md",
        implementation / "requirements" / "phase8_brid.txt",
        implementation / "scripts" / "build_phase8_release.py",
        implementation / "scripts" / "run_phase8_brid_export.py",
        implementation / "src" / "devoteam_reference_ai" / "__init__.py",
        implementation / "src" / "devoteam_reference_ai" / "phase8_brid_export.py",
        implementation / "tests" / "test_phase8_brid_export.py",
    ]
    deliverable_names = [
        "BRID_REFERENCE_DOSSIER_AUDITED.docx",
        "BRID_REFERENCE_DOSSIER_AUDITED.pdf",
        "BRID_REFERENCE_DOSSIER_DATA.json",
        "PHASE_7_BRID_SHORTLIST_APPROVAL.json",
        "PHASE_8_BRID_MANIFEST.json",
        "PHASE_8_BRID_REPORT.md",
        "SHA256SUMS.txt",
        "_SUCCESS.json",
    ]
    deliverable_files = [deliverables / name for name in deliverable_names]

    missing = [str(path) for path in source_files + deliverable_files if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing release files:\n" + "\n".join(missing))

    entries: list[tuple[str, Path]] = []
    for path in source_files:
        relative = path.relative_to(implementation)
        entries.append((f"implementation/{relative.as_posix()}", path))
    for path in deliverable_files:
        entries.append((f"deliverables/{path.name}", path))
    entries.sort(key=lambda item: item[0])

    manifest = {
        "schema_version": 1,
        "phase": 8,
        "pipeline_version": "phase8_brid_audited_export_v2",
        "label": "SYNTHETIC_TEST_ONLY",
        "status": "TECHNICAL_PASS_AUDITED_EXPORT_COMPLETE",
        "production_promotion_allowed": False,
        "files": [
            {
                "path": archive_path,
                "bytes": source_path.stat().st_size,
                "sha256": sha256(source_path),
            }
            for archive_path, source_path in entries
        ],
    }
    manifest_bytes = (
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")

    manifest_path = output_dir / "PHASE_8_BRID_RELEASE_MANIFEST.json"
    manifest_path.write_bytes(manifest_bytes)

    package_path = output_dir / "PHASE_8_BRID_AUDITED_EXPORT_RELEASE.zip"
    with ZipFile(package_path, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        manifest_info = ZipInfo("PHASE_8_BRID_RELEASE_MANIFEST.json", FIXED_ZIP_TIME)
        manifest_info.compress_type = ZIP_DEFLATED
        manifest_info.external_attr = 0o644 << 16
        archive.writestr(manifest_info, manifest_bytes)

        for archive_path, source_path in entries:
            info = ZipInfo(archive_path, FIXED_ZIP_TIME)
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, source_path.read_bytes())

    print(
        json.dumps(
            {
                "manifest": str(manifest_path),
                "package": str(package_path),
                "package_bytes": package_path.stat().st_size,
                "package_sha256": sha256(package_path),
                "packaged_files": len(entries),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
