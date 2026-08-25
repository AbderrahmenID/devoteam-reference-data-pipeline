from __future__ import annotations

import argparse
import json
from pathlib import Path

from devoteam_reference_ai.phase7_brid_matching import (
    PinnedE5QueryAdapter,
    run_phase7_brid,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the synthetic BRID Phase 7 hybrid matching case."
    )
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument(
        "--mode",
        choices=("hybrid", "bm25"),
        default="hybrid",
        help="bm25 is permitted only for a local mechanical dry run.",
    )
    args = parser.parse_args()
    project_root = args.project_root.resolve()
    adapter = None
    if args.mode == "hybrid":
        adapter = PinnedE5QueryAdapter(
            project_root / "config" / "phase5_retrieval.yaml"
        )
    run_root, manifest = run_phase7_brid(
        project_root=project_root,
        config_path=project_root
        / "config"
        / "phase7_brid_controlled_case.yaml",
        embedding_adapter=adapter,
        mode_override=args.mode,
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(f"RUN_ROOT={run_root}")


if __name__ == "__main__":
    main()
