from __future__ import annotations

import json
from pathlib import Path

import openpyxl
import pytest
import yaml

from devoteam_reference_ai.phase6_opportunity import (
    OpportunityAnalysisError,
    SourceSegment,
    analyze_opportunity,
    build_retrieval_query,
    classify_requirement,
    compile_filter_proposals,
    create_redacted_sample,
    create_review_workbook,
    detect_language,
    extract_opportunity_segments,
    extract_requirements,
    load_phase6_config,
    normalize_text,
    sanitize_opportunity_text,
    sha256_file,
    validate_filter_proposals,
    verify_phase5_dependency,
    verify_phase6_run,
    write_analysis_run,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "phase6_opportunity.yaml"


@pytest.fixture()
def config() -> dict:
    return load_phase6_config(CONFIG_PATH)


@pytest.fixture()
def filter_values() -> dict:
    return {
        "country": {"Tunisie": 12, "Libye": 3},
        "business_unit": {"Digital": 8},
        "client": {"BTS Bank": 2},
        "sector": {"Banque": 15},
        "service_nature": {"Conseil": 20},
        "offering": {"Stratégie digitale": 7},
        "project_year": {"2019": 4, "2020": 5},
        "attestation_available": {"Oui": 10},
        "document_type": {"CONTRACT": 10},
        "data_quality_status": {"GOOD": 10},
    }


def test_config_loads_and_keeps_llm_blocked(config):
    assert config["phase"] == 6
    assert config["security"]["external_llm_enabled"] is False
    assert config["filters"]["human_confirmation_required"] is True


@pytest.mark.parametrize(
    "field,value",
    [
        ("external_llm_enabled", True),
        ("raw_opportunity_logging_allowed", True),
        ("security_filters_disableable", True),
    ],
)
def test_security_configuration_cannot_be_weakened(tmp_path, config, field, value):
    changed = json.loads(json.dumps(config))
    changed["security"][field] = value
    path = tmp_path / "bad.yaml"
    path.write_text(yaml.safe_dump(changed, allow_unicode=True), encoding="utf-8")
    with pytest.raises(ValueError):
        load_phase6_config(path)


def test_hidden_or_unconfirmed_filter_policy_is_rejected(tmp_path, config):
    changed = json.loads(json.dumps(config))
    changed["filters"]["human_confirmation_required"] = False
    path = tmp_path / "bad.yaml"
    path.write_text(yaml.safe_dump(changed, allow_unicode=True), encoding="utf-8")
    with pytest.raises(ValueError):
        load_phase6_config(path)


def test_normalization_is_accent_and_case_robust():
    assert normalize_text("STRATÉGIE  Digitale") == "strategie digitale"


def test_sensitive_minimization_masks_contact_and_money():
    value = sanitize_opportunity_text("a.b@example.com +216 98 123 456 budget 120 000 EUR")
    assert "example.com" not in value
    assert "+216" not in value
    assert "120 000" not in value
    assert "[EMAIL]" in value and "[PHONE]" in value and "[MONETARY_VALUE]" in value


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Le prestataire doit fournir une référence pour la mission.", "fr"),
        ("The provider must demonstrate relevant project experience.", "en"),
        ("يجب على المزود تقديم خبرة ومراجع في القطاع البنكي.", "ar"),
    ],
)
def test_language_detection(text, expected):
    assert detect_language(text) == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Le prestataire doit fournir une référence.", "MUST"),
        ("Une expérience bancaire est souhaitée.", "SHOULD"),
        ("La certification constitue un atout.", "PREFERRED"),
        ("La mission concerne une stratégie digitale.", "CONTEXT"),
        ("يجب تقديم مرجع في القطاع البنكي.", "MUST"),
    ],
)
def test_requirement_classification(config, text, expected):
    assert classify_requirement(text, config) == expected


def test_text_input_extraction(tmp_path, config):
    path = tmp_path / "input.txt"
    path.write_text("Le prestataire doit fournir une référence bancaire.", encoding="utf-8")
    segments = extract_opportunity_segments(path, config)
    assert len(segments) == 1 and segments[0].locator == "text:1"


def test_unsupported_input_format_is_rejected(tmp_path, config):
    path = tmp_path / "input.csv"
    path.write_text("x", encoding="utf-8")
    with pytest.raises(OpportunityAnalysisError):
        extract_opportunity_segments(path, config)


def test_duplicate_units_are_removed(config):
    segments = [
        SourceSegment("Le prestataire doit fournir une référence.\nLe prestataire doit fournir une référence.", "text:1", None)
    ]
    rows = extract_requirements(segments, "a" * 64, config)
    assert len(rows) == 1
    assert rows[0]["human_review_required"] is True
    assert rows[0]["approved"] is False


def test_country_alias_and_sector_compile_visible_hard_candidates(config, filter_values):
    requirements = [
        {
            "requirement_id": "REQ-1",
            "requirement_text": "The provider must show a Banque reference in Tunisia.",
            "classification": "MUST",
        }
    ]
    proposals = compile_filter_proposals(requirements, filter_values, config)
    pairs = {(row["field"], row["value"], row["proposed_behavior"]) for row in proposals}
    assert ("country", "Tunisie", "HARD_CANDIDATE") in pairs
    assert ("sector", "Banque", "HARD_CANDIDATE") in pairs
    assert all(row["visible_to_user"] and row["requires_human_confirmation"] for row in proposals)
    assert not any(row["confirmed"] for row in proposals)


def test_context_never_becomes_hard_filter(config, filter_values):
    requirements = [
        {
            "requirement_id": "REQ-1",
            "requirement_text": "La mission se déroule en Tunisie dans le secteur Banque.",
            "classification": "CONTEXT",
        }
    ]
    proposals = compile_filter_proposals(requirements, filter_values, config)
    assert proposals
    assert {row["proposed_behavior"] for row in proposals} == {"CONTEXT_ONLY"}


def test_preferred_values_are_soft(config, filter_values):
    requirements = [
        {
            "requirement_id": "REQ-1",
            "requirement_text": "Une expérience en Tunisie est souhaitée.",
            "classification": "SHOULD",
        }
    ]
    proposals = compile_filter_proposals(requirements, filter_values, config)
    assert proposals[0]["proposed_behavior"] == "SOFT_PREFERENCE"


def test_exclusion_marker_creates_exclusion_candidate(config, filter_values):
    requirements = [
        {
            "requirement_id": "REQ-1",
            "requirement_text": "Exclure les références en Libye.",
            "classification": "CONTEXT",
        }
    ]
    proposals = compile_filter_proposals(requirements, filter_values, config)
    assert proposals[0]["proposed_behavior"] == "EXCLUSION_CANDIDATE"


def test_year_since_experience_becomes_year_after(config, filter_values):
    requirements = [
        {
            "requirement_id": "REQ-1",
            "requirement_text": "Le prestataire doit fournir une référence de projet depuis 2019.",
            "classification": "MUST",
        }
    ]
    proposals = compile_filter_proposals(requirements, filter_values, config)
    assert any(row["field"] == "year_after" and row["value"] == 2019 for row in proposals)
    assert not any(row["field"] == "project_year" for row in proposals)


def test_unknown_filter_value_is_not_invented(config, filter_values):
    requirements = [
        {
            "requirement_id": "REQ-1",
            "requirement_text": "Le prestataire doit intervenir au Japon.",
            "classification": "MUST",
        }
    ]
    assert compile_filter_proposals(requirements, filter_values, config) == []


def test_forbidden_filter_is_rejected(config):
    with pytest.raises(AssertionError):
        validate_filter_proposals(
            [
                {
                    "field": "project value",
                    "proposed_behavior": "HARD_CANDIDATE",
                    "visible_to_user": True,
                    "requires_human_confirmation": True,
                    "confirmed": False,
                    "status": "PROPOSED",
                }
            ],
            config,
        )


def test_retrieval_query_prioritizes_must(config):
    rows = [
        {"classification": "CONTEXT", "source_locator": "1", "requirement_text": "context"},
        {"classification": "MUST", "source_locator": "2", "requirement_text": "must"},
    ]
    assert build_retrieval_query(rows).splitlines()[0] == "must"


def test_review_workbook_is_complete(tmp_path):
    analysis = {
        "opportunity_id": "OPP-1",
        "source_file_name": "x.txt",
        "source_sha256": "a" * 64,
        "analysis_mode": "deterministic",
        "external_llm_calls": 0,
        "status": "READY_FOR_HUMAN_REVIEW",
        "requirements": [
            {
                "requirement_id": "REQ-1",
                "classification": "MUST",
                "language": "fr",
                "requirement_text": "Le prestataire doit fournir une référence.",
                "source_locator": "text:1",
                "page_number_1_based": None,
            }
        ],
        "filter_proposals": [],
    }
    path = tmp_path / "review.xlsx"
    create_review_workbook(path, analysis)
    workbook = openpyxl.load_workbook(path)
    assert workbook.sheetnames == ["Overview", "Requirements", "Filters"]
    assert workbook["Requirements"]["G2"].value == "PENDING"


def test_phase5_dependency_verifies_hashes(tmp_path, config):
    phase5 = tmp_path / "phase5"
    phase5.mkdir()
    manifest = {
        "snapshot_id": config["input"]["snapshot_id"],
        "status": "TECHNICAL_PASS",
        "qa_gate": "PASS",
        "external_llm_calls": 0,
        "raw_user_query_log_rows": 0,
    }
    manifest_path = phase5 / "PHASE_5_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    sums_path = phase5 / "SHA256SUMS.txt"
    sums_path.write_text("x", encoding="utf-8")
    changed = json.loads(json.dumps(config))
    changed["input"]["expected_phase5_manifest_sha256"] = sha256_file(manifest_path)
    changed["input"]["expected_phase5_sha256sums_sha256"] = sha256_file(sums_path)
    (phase5 / "_SUCCESS.json").write_text(
        json.dumps({"manifest_sha256": sha256_file(manifest_path)}), encoding="utf-8"
    )
    assert verify_phase5_dependency(phase5, changed)["manifest"]["qa_gate"] == "PASS"


def test_end_to_end_analysis_and_signed_run(tmp_path, config, filter_values):
    input_path = tmp_path / "OPPORTUNITY_INPUT.txt"
    create_redacted_sample(input_path)
    filter_path = tmp_path / "filter_values.json"
    filter_path.write_text(json.dumps(filter_values, ensure_ascii=False), encoding="utf-8")
    changed = json.loads(json.dumps(config))
    changed["input"]["expected_filter_values_sha256"] = sha256_file(filter_path)
    analysis = analyze_opportunity(input_path, filter_path, changed)
    assert analysis["requirements"]
    assert analysis["external_llm_calls"] == 0
    assert analysis["business_filters_auto_applied"] == 0
    run_root, manifest = write_analysis_run(
        input_path=input_path,
        filter_values_path=filter_path,
        output_root=tmp_path / "outputs",
        config=changed,
        input_mode="SAMPLE_REDACTED",
    )
    assert manifest["status"] == "TECHNICAL_PASS_READY_FOR_HUMAN_REVIEW"
    assert (run_root / "OPPORTUNITY_REVIEW.xlsx").exists()
    assert verify_phase6_run(run_root, changed)["manifest"]["external_llm_calls"] == 0
    second_root, second_manifest = write_analysis_run(
        input_path=input_path,
        filter_values_path=filter_path,
        output_root=tmp_path / "outputs",
        config=changed,
        input_mode="SAMPLE_REDACTED",
    )
    assert second_root == run_root and second_manifest == manifest
