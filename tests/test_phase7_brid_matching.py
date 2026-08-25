from __future__ import annotations

import copy
import hashlib
from pathlib import Path

import numpy as np
import openpyxl
import pandas as pd
import pytest

from devoteam_reference_ai.phase7_brid_matching import (
    annotate_portfolio_capabilities,
    evaluate_portfolio_rules,
    load_approved_brid_review,
    load_phase7_brid_config,
    run_phase7_brid,
    select_portfolio,
    verify_phase5_2_inputs,
    verify_phase7_brid_run,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "phase7_brid_controlled_case.yaml"
WORKBOOK_PATH = (
    ROOT
    / "data"
    / "opportunities"
    / "OPP-2098dd1874292d22"
    / "phase6_brid_controlled_case_v2"
    / "BRID_PHASE_6_REVIEW.xlsx"
)


@pytest.fixture()
def config() -> dict:
    return load_phase7_brid_config(CONFIG_PATH)


def test_configuration_preserves_security_and_scoring_boundaries(config):
    assert config["retrieval"]["mode"] == "hybrid"
    assert config["retrieval"]["lexical_weight"] == pytest.approx(0.9)
    assert config["retrieval"]["dense_weight"] == pytest.approx(0.1)
    assert config["scoring"]["tender_points_total"] == 100
    assert config["scoring"]["points_awarded_automatically"] is False
    assert config["promotion"]["production_promotion_allowed"] is False


def test_approved_workbook_loads_all_four_human_gates(config):
    review = load_approved_brid_review(WORKBOOK_PATH, config)
    assert len(review["requirements"]) == 16
    assert len(review["eligibility_rules"]) == 7
    assert len(review["scoring_criteria"]) == 6
    assert len(review["filters"]) == 11
    assert len(review["match_requirements"]) == 11
    assert len(review["policy_requirements"]) == 2
    assert len(review["non_retrieval_requirements"]) == 3
    assert sum(row["points"] for row in review["scoring_criteria"]) == 100


def test_portfolio_constraints_are_not_global_filters(config):
    review = load_approved_brid_review(WORKBOOK_PATH, config)
    assert review["hard_filters"] == {
        "evidence_available": True,
        "evidence_type": ["ATTESTATION_ORIGINAL", "ATTESTATION_SCAN"],
    }
    assert {row["field"] for row in review["portfolio_filters"]} == {
        "year_start",
        "sector_code",
        "region",
    }
    assert len(review["user_facets"]) == 7


def test_pending_review_decision_fails_closed(tmp_path, config):
    changed = tmp_path / "review.xlsx"
    workbook = openpyxl.load_workbook(WORKBOOK_PATH)
    headers = [cell.value for cell in workbook["Requirements"][1]]
    decision_column = headers.index("reviewer_decision") + 1
    workbook["Requirements"].cell(2, decision_column).value = "PENDING"
    workbook.save(changed)
    changed_config = copy.deepcopy(config)
    changed_config["input"]["expected_review_workbook_sha256"] = hashlib.sha256(
        changed.read_bytes()
    ).hexdigest()
    with pytest.raises(Exception, match="Pending review decision"):
        load_approved_brid_review(changed, changed_config)


def _candidate_rows() -> pd.DataFrame:
    base = {
        "country_code": "TN",
        "subregion": "Afrique du Nord",
        "evidence_available": True,
        "evidence_type": "ATTESTATION_SCAN",
        "base_shortlist_eligible": True,
        "capability_tags_json": "[]",
        "technology_tags_json": "[]",
        "engagement_tags_json": "[]",
        "year_start": 2021,
        "year_end": 2021,
        "duplicate_group_id": "",
        "must_covered": 1,
        "must_total": 1,
    }
    rows = [
        {
            **base,
            "reference_id": "S1",
            "client_raw": "Bank 1",
            "sector_code": "BANKING",
            "offering_code": "IT_STRATEGY_AMOA",
            "engagement_tags_json": '["AMOA", "IMPLEMENTATION"]',
            "final_score": 0.95,
            "final_rank": 1,
        },
        {
            **base,
            "reference_id": "S2",
            "client_raw": "Bank 2",
            "sector_code": "BANKING",
            "offering_code": "IT_STRATEGY",
            "final_score": 0.90,
            "final_rank": 2,
        },
        {
            **base,
            "reference_id": "S3",
            "client_raw": "Industry",
            "sector_code": "INDUSTRY",
            "offering_code": "IT_STRATEGY",
            "final_score": 0.85,
            "final_rank": 3,
        },
        {
            **base,
            "reference_id": "P1",
            "client_raw": "PCA",
            "sector_code": "BANKING",
            "offering_code": "BUSINESS_CONTINUITY",
            "capability_tags_json": '["BUSINESS_CONTINUITY"]',
            "final_score": 0.80,
            "final_rank": 4,
        },
        {
            **base,
            "reference_id": "P2",
            "client_raw": "PCA 2",
            "sector_code": "INSURANCE",
            "offering_code": "BUSINESS_CONTINUITY",
            "capability_tags_json": '["BUSINESS_CONTINUITY"]',
            "final_score": 0.75,
            "final_rank": 5,
        },
        {
            **base,
            "reference_id": "C1",
            "client_raw": "Cyber",
            "sector_code": "BANKING",
            "offering_code": "CYBERSECURITY",
            "capability_tags_json": '["CYBERSECURITY"]',
            "final_score": 0.70,
            "final_rank": 6,
        },
        {
            **base,
            "reference_id": "C2",
            "client_raw": "Cyber 2",
            "sector_code": "INSURANCE",
            "offering_code": "CYBERSECURITY",
            "capability_tags_json": '["CYBERSECURITY"]',
            "final_score": 0.65,
            "final_rank": 7,
        },
    ]
    return pd.DataFrame(rows)


def test_capability_annotation_and_portfolio_rules(config):
    review = load_approved_brid_review(WORKBOOK_PATH, config)
    candidates = annotate_portfolio_capabilities(_candidate_rows())
    assert candidates["is_signed_attestation"].all()
    assert int(candidates["is_sdsi"].sum()) == 3
    assert int(candidates["is_pca"].sum()) == 2
    assert int(candidates["is_security"].sum()) == 2
    results = evaluate_portfolio_rules(candidates, review["eligibility_rules"])
    assert all(row["passed"] for row in results)


def test_portfolio_selector_satisfies_count_rules(config):
    review = load_approved_brid_review(WORKBOOK_PATH, config)
    candidates = annotate_portfolio_capabilities(_candidate_rows())
    coverage = pd.DataFrame(
        [
            {
                "reference_id": row.reference_id,
                "requirement_id": requirement["requirement_id"],
                "classification": requirement["classification"],
                "covered": True,
            }
            for row in candidates.itertuples()
            for requirement in review["match_requirements"][:1]
        ]
    )
    selected = select_portfolio(
        candidates,
        coverage,
        review["eligibility_rules"],
        config,
    )
    results = evaluate_portfolio_rules(selected, review["eligibility_rules"])
    assert all(row["passed"] for row in results)
    assert len(selected) <= config["eligibility"]["maximum_portfolio_references"]


def test_phase5_2_signed_inputs_are_reproducible(config):
    verified = verify_phase5_2_inputs(ROOT, config)
    assert verified["manifest"]["qa_gate"] == "PASS"
    assert verified["manifest"]["citation_correctness_status"] == "PENDING_HUMAN_AUDIT"
    assert verified["quality_gate"]["technical_gate"] == "PASS"


def test_actual_data_bm25_dry_run_is_complete_and_safe(tmp_path):
    output = tmp_path / "phase7_brid_dry_run"
    run_root, manifest = run_phase7_brid(
        project_root=ROOT,
        config_path=CONFIG_PATH,
        embedding_adapter=None,
        mode_override="bm25",
        output_root=output,
    )
    assert run_root == output
    assert manifest["status"] == "TECHNICAL_DRY_RUN_BM25_ONLY"
    assert manifest["external_embedding_api_calls"] == 0
    assert manifest["external_llm_calls"] == 0
    assert manifest["points_awarded_automatically"] == 0
    assert manifest["technical_threshold_status"] == "PENDING_HUMAN_SCORING"
    assert manifest["candidate_references"] > 0
    verification = verify_phase7_brid_run(
        run_root,
        load_phase7_brid_config(CONFIG_PATH),
    )
    assert verification["quality_gate"]["technical_gate"] == "PASS"


def test_actual_data_hybrid_path_uses_local_vectors_only(tmp_path):
    class DeterministicLocalAdapter:
        def encode_queries(self, texts):
            vectors = []
            for text in texts:
                seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:16], 16)
                random = np.random.default_rng(seed)
                vector = random.standard_normal(768).astype(np.float32)
                vector /= np.linalg.norm(vector)
                vectors.append(vector)
            return np.asarray(vectors, dtype=np.float32)

    run_root, manifest = run_phase7_brid(
        project_root=ROOT,
        config_path=CONFIG_PATH,
        embedding_adapter=DeterministicLocalAdapter(),
        output_root=tmp_path / "hybrid_mechanical_test",
    )
    assert manifest["status"] == "TECHNICAL_PASS_READY_FOR_EVIDENCE_AUDIT"
    assert manifest["retrieval_mode"] == "hybrid"
    assert manifest["local_query_embedding_calls"] == 11
    assert manifest["external_embedding_api_calls"] == 0
    assert manifest["portfolio_rules_passed"] == 7
    assert manifest["must_requirements_covered"] == manifest["must_requirements_total"]
    assert verify_phase7_brid_run(
        run_root,
        load_phase7_brid_config(CONFIG_PATH),
    )["quality_gate"]["technical_gate"] == "PASS"
