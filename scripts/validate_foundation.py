#!/usr/bin/env python3
"""Validate the Phase 1 configuration and create a reproducible run manifest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    arguments = parser.parse_args()

    project_root = arguments.project_root.expanduser().resolve()
    sys.path.insert(0, str(project_root / "src"))

    from devoteam_reference_ai.config import load_project_configuration
    from devoteam_reference_ai.paths import ProjectPaths
    from devoteam_reference_ai.run_context import new_run_context, write_run_manifest

    configuration = load_project_configuration(project_root)
    paths = ProjectPaths.from_root(project_root)
    paths.create_runtime_directories()
    context = new_run_context("phase1_foundation", project_root)
    manifest_path = paths.manifests / f"{context.run_id}.json"
    write_run_manifest(
        context,
        manifest_path,
        project_root,
        extra={
            "phase_zero_decisions": ["A1", "B1", "C1", "D1", "E1", "F1", "G1"],
            "source_access_mode": configuration["project"]["drive"]["source_access_mode"],
            "external_llm_enabled": configuration["security"]["external_llm"]["enabled"],
            "status": "PASS",
        },
    )
    print(
        json.dumps(
            {
                "status": "PASS",
                "project_root": str(project_root),
                "run_id": context.run_id,
                "manifest": str(manifest_path),
                "config_files": sorted(context.config_hashes),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
