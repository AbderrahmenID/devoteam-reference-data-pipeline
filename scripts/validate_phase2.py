from __future__ import annotations

import argparse
import json
from pathlib import Path

from devoteam_reference_ai.phase2_pipeline import load_phase2_config, verify_snapshot


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path)
    args = parser.parse_args()
    root = args.project_root.resolve()
    config = load_phase2_config(root / "config" / "phase2_source.yaml")
    result = {"config": "PASS", "source_access_mode": config["source"]["access_mode"]}
    if args.snapshot:
        result["snapshot"] = verify_snapshot(args.snapshot)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
