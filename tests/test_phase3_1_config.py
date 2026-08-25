from pathlib import Path

from devoteam_reference_ai.phase3_1_repair import load_phase3_1_config


def test_phase3_1_config_is_pinned_and_llm_disabled():
    root = Path(__file__).resolve().parents[1]
    config = load_phase3_1_config(root / "config" / "phase3_1_repair.yaml")
    assert config["input"]["expected_total_pages"] == 408
    assert config["input"]["expected_target_pages"] == 21
    assert config["input"]["expected_review_pages"] == 17
    assert config["input"]["expected_failed_pages"] == 4
    assert config["security"]["external_llm_enabled"] is False
