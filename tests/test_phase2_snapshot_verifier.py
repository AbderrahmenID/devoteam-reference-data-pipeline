import json
from pathlib import Path

import pytest

from devoteam_reference_ai.phase2_pipeline import verify_snapshot
from devoteam_reference_ai.phase2_utils import sha256_file


def test_snapshot_requires_success_marker(tmp_path: Path):
    with pytest.raises(AssertionError):
        verify_snapshot(tmp_path)


def test_snapshot_hash_verification(tmp_path: Path):
    raw = tmp_path / "raw.bin"
    raw.write_bytes(b"immutable")
    manifest = {"status": "PASS", "source_mutation_calls": 0}
    (tmp_path / "SNAPSHOT_MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")
    (tmp_path / "_SUCCESS.json").write_text("{}", encoding="utf-8")
    (tmp_path / "SHA256SUMS.txt").write_text(f"{sha256_file(raw)}  raw.bin\n", encoding="utf-8")
    assert verify_snapshot(tmp_path)["status"] == "PASS"
    raw.write_bytes(b"changed")
    with pytest.raises(AssertionError):
        verify_snapshot(tmp_path)
