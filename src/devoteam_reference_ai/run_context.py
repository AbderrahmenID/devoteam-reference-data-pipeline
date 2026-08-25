"""Reproducible run identifiers and lineage manifests."""

from __future__ import annotations

import json
import platform
import sys
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .hashing import sha256_file
from .paths import assert_safe_write_path


@dataclass(frozen=True)
class RunContext:
    run_id: str
    stage: str
    started_at_utc: str
    python_version: str
    platform: str
    config_hashes: dict[str, str]


def new_run_context(stage: str, project_root: str | Path) -> RunContext:
    now = datetime.now(timezone.utc)
    run_id = f"{now.strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
    config_dir = Path(project_root) / "config"
    hashes = {
        path.name: sha256_file(path)
        for path in sorted(config_dir.glob("*.yaml"))
    }
    return RunContext(
        run_id=run_id,
        stage=stage,
        started_at_utc=now.isoformat(),
        python_version=sys.version.split()[0],
        platform=platform.platform(),
        config_hashes=hashes,
    )


def write_run_manifest(
    context: RunContext,
    output_path: str | Path,
    project_root: str | Path,
    extra: dict[str, object] | None = None,
) -> Path:
    safe_output = assert_safe_write_path(output_path, project_root)
    safe_output.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(context)
    if extra:
        payload["extra"] = extra
    safe_output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return safe_output
