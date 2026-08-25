from pathlib import Path

import pytest

from devoteam_reference_ai.phase3_pipeline import load_phase3_config


def test_phase3_config_is_pinned_and_llm_disabled():
    root = Path(__file__).resolve().parents[1]
    config = load_phase3_config(root / "config" / "phase3_extraction.yaml")
    assert config["input"]["snapshot_id"] == "20260714T154731Z_129ff982c8"
    assert config["input"]["expected_downloaded_documents"] == 134
    assert config["extraction"]["ocr_languages"] == "fra+eng+ara"
    assert config["security"]["external_llm_enabled"] is False
