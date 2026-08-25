from __future__ import annotations

import json
from pathlib import Path

import pytest

from devoteam_reference_ai.phase8_brid_export import (
    LABEL,
    MISSION_COPY,
    STATUS,
    build_pre_pdf_outputs,
    load_approval,
    load_audited_case,
    load_phase8_config,
    sha256_file,
    verify_audit_workbook,
    verify_reference_template,
    verify_run,
)


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
CONFIG = ROOT / "config" / "phase8_brid_audited_export.yaml"
if (WORKSPACE / "phase8_work").is_dir():
    APPROVAL = ROOT / "approval" / "PHASE_7_BRID_SHORTLIST_APPROVAL.json"
    AUDIT = WORKSPACE / "phase8_work" / "BRID_PHASE_7_EVIDENCE_AUDIT.xlsx"
    TEMPLATE = WORKSPACE / "phase8_work" / "REFERENCE_TEMPLATE.docx"
    OUTPUT = WORKSPACE / "outputs" / "phase8_brid_audited_export"
else:
    APPROVAL = ROOT / "human_inputs" / "phase8" / "PHASE_7_BRID_SHORTLIST_APPROVAL.json"
    AUDIT = ROOT / "BRID_PHASE_7_EVIDENCE_AUDIT.xlsx"
    TEMPLATE = ROOT / "human_inputs" / "phase8" / "REFERENCE_TEMPLATE.docx"
    OUTPUT = ROOT


@pytest.fixture(scope="module")
def config() -> dict:
    return load_phase8_config(CONFIG)


@pytest.fixture(scope="module")
def audited_case(config) -> dict:
    audit = verify_audit_workbook(AUDIT, config)
    approval = load_approval(APPROVAL, config, audit["sha256"])
    return load_audited_case(AUDIT, config, approval)


def test_configuration_is_synthetic_and_secure(config):
    assert config["label"] == LABEL
    assert config["generation"]["mode"] == "deterministic_audited_export"
    assert config["generation"]["external_llm_enabled"] is False
    assert config["generation"]["external_translation_enabled"] is False
    assert config["generation"]["automatic_client_delivery"] is False
    assert config["generation"]["automatic_tender_scoring"] is False
    assert config["generation"]["production_promotion_allowed"] is False


def test_audit_workbook_is_hash_bound(config):
    result = verify_audit_workbook(AUDIT, config)
    assert result["sha256"] == config["inputs"]["audit_workbook_sha256"]
    assert result["size_bytes"] == config["inputs"]["audit_workbook_size_bytes"]


def test_template_is_hash_and_structure_bound(config):
    result = verify_reference_template(TEMPLATE, config)
    assert result["sha256"] == config["inputs"]["reference_template_sha256"]
    assert result["structure_verified"] is True
    assert result["reference_slots"] >= 17


def test_approval_is_bound_without_invented_identity(config):
    audit = verify_audit_workbook(AUDIT, config)
    approval = load_approval(APPROVAL, config, audit["sha256"])
    assert approval["approval_status"] == "APPROVED"
    assert approval["approver_identity_recorded"] is False
    assert approval["source_workbook_sha256"] == sha256_file(AUDIT)


def test_shortlist_contract(audited_case):
    assert audited_case["status"] == STATUS
    assert len(audited_case["records"]) == 10
    assert {row["reference_id"] for row in audited_case["records"]} == set(
        MISSION_COPY
    )
    assert all(row["citation_support"] == "SUPPORTED" for row in audited_case["records"])
    assert all("#page=" in row["source_url"] for row in audited_case["records"])


@pytest.mark.parametrize(
    ("metric", "expected"),
    [
        ("eligibility_passed", 7),
        ("eligibility_total", 7),
        ("must_covered", 8),
        ("must_total", 8),
        ("should_covered", 2),
        ("should_total", 3),
        ("points_available", 100),
        ("points_awarded", 0),
    ],
)
def test_key_metrics(audited_case, metric, expected):
    assert audited_case["metrics"][metric] == expected


def test_explicit_gap_is_preserved(audited_case):
    assert audited_case["metrics"]["explicit_gaps"] == ["SCOPE-CLOUD"]


def test_citation_adjudication_contract(audited_case):
    assert audited_case["citation_stats"] == {
        "total": 203,
        "SUPPORTED": 79,
        "PARTIAL": 24,
        "UNSUPPORTED": 100,
    }


def test_no_tender_points_are_awarded(audited_case):
    assert all(
        row.get("points_awarded") in (None, "")
        for row in audited_case["scoring"]
    )
    assert audited_case["metrics"]["points_awarded"] == 0


def test_each_reference_has_audited_requirement_coverage(audited_case):
    assert all(row["covered_requirements"] for row in audited_case["records"])
    cloud_claims = [
        requirement
        for row in audited_case["records"]
        for requirement in row["covered_requirements"]
        if requirement["code"] == "SCOPE-CLOUD"
    ]
    assert cloud_claims == []


def test_pre_pdf_outputs_build(tmp_path, config):
    _, data, template = build_pre_pdf_outputs(
        audit_workbook=AUDIT,
        reference_template=TEMPLATE,
        approval_path=APPROVAL,
        config_path=CONFIG,
        output_dir=tmp_path,
    )
    outputs = config["output"]
    assert (tmp_path / outputs["docx_name"]).exists()
    assert (tmp_path / outputs["data_name"]).exists()
    assert (tmp_path / outputs["report_name"]).exists()
    assert data["metrics"]["selected_references"] == 10
    assert template["structure_verified"] is True


def test_final_release_if_present(config):
    success = OUTPUT / config["output"]["success_name"]
    if not success.exists():
        pytest.skip("Final PDF/visual-QA release not built yet")
    result = verify_run(output_dir=OUTPUT, config_path=CONFIG)
    assert result["manifest"]["status"] == STATUS
    assert result["manifest"]["visual_qa_status"] == "PASSED"
    assert json.loads(success.read_text(encoding="utf-8"))["status"].startswith(
        "COMPLETE_REPRODUCIBLE"
    )
