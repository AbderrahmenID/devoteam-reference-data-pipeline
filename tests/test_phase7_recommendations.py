from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import openpyxl
import pandas as pd
import pytest
import yaml

from devoteam_reference_ai.phase5_bm25 import BM25Index
from devoteam_reference_ai.phase7_recommendations import (
    RecommendationError,
    SecureBM25Retriever,
    _recency_score,
    _soft_preference_score,
    create_recommendation_workbook,
    diversify_recommendations,
    eligible_reference_ids,
    load_phase7_config,
    requirement_gap_summary,
    score_references,
    validate_evidence,
    verify_phase5_index,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "phase7_recommendations.yaml"


@pytest.fixture()
def config() -> dict:
    return load_phase7_config(CONFIG_PATH)


def _phase5_filter_config() -> dict:
    return {
        "filters": {
            "security_field": "security_classification",
            "supported_exact": {"sector": "sector_values_json"},
            "supported_ranges": {"year_after": "project_year_values_json", "year_before": "project_year_values_json"},
        }
    }


def _chunks() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "vector_row": 0,
                "chunk_id": "C1",
                "document_id": "D1",
                "chunk_text": "stratégie digitale banque gouvernance",
                "security_classification": "INTERNAL",
                "sector_values_json": '["Banque"]',
                "project_year_values_json": '["2021"]',
            },
            {
                "vector_row": 1,
                "chunk_id": "C2",
                "document_id": "D2",
                "chunk_text": "agriculture logistique",
                "security_classification": "INTERNAL",
                "sector_values_json": '["Agriculture"]',
                "project_year_values_json": '["2018"]',
            },
            {
                "vector_row": 2,
                "chunk_id": "C3",
                "document_id": "D3",
                "chunk_text": "stratégie banque",
                "security_classification": "CONFIDENTIAL",
                "sector_values_json": '["Banque"]',
                "project_year_values_json": '["2022"]',
            },
        ]
    )


def test_configuration_loads_secure_baseline(config):
    assert config["retrieval"]["mode"] == "bm25_secure_baseline"
    assert config["retrieval"]["cross_encoder_enabled"] is False
    assert config["promotion"]["automatic_production_promotion"] is False


@pytest.mark.parametrize(
    "field",
    [
        "external_llm_enabled",
        "external_embedding_api_enabled",
        "raw_opportunity_logging_allowed",
        "security_filters_disableable",
    ],
)
def test_security_configuration_cannot_be_weakened(tmp_path, config, field):
    changed = json.loads(json.dumps(config))
    changed["security"][field] = True
    path = tmp_path / "bad.yaml"
    path.write_text(yaml.safe_dump(changed), encoding="utf-8")
    with pytest.raises(ValueError):
        load_phase7_config(path)


def test_cross_encoder_cannot_be_enabled_in_signed_baseline(tmp_path, config):
    changed = json.loads(json.dumps(config))
    changed["retrieval"]["cross_encoder_enabled"] = True
    path = tmp_path / "bad.yaml"
    path.write_text(yaml.safe_dump(changed), encoding="utf-8")
    with pytest.raises(ValueError):
        load_phase7_config(path)


def test_component_weights_must_sum_to_one(tmp_path, config):
    changed = json.loads(json.dumps(config))
    changed["scoring"]["component_weights"]["relevance"] = 0.2
    path = tmp_path / "bad.yaml"
    path.write_text(yaml.safe_dump(changed), encoding="utf-8")
    with pytest.raises(ValueError):
        load_phase7_config(path)


def test_secure_retriever_applies_security_and_hard_filters_before_scoring():
    chunks = _chunks()
    bm25 = BM25Index.build(chunks["chunk_text"])
    retriever = SecureBM25Retriever(chunks, bm25, _phase5_filter_config())
    results = retriever.search(
        "stratégie banque",
        allowed_security_classifications=["INTERNAL"],
        hard_filters={"sector": "Banque", "year_after": 2020},
        top_k=10,
        minimum_score=0.0,
    )
    assert results["chunk_id"].tolist() == ["C1"]


def test_security_authorization_is_mandatory():
    chunks = _chunks()
    retriever = SecureBM25Retriever(chunks, BM25Index.build(chunks["chunk_text"]), _phase5_filter_config())
    with pytest.raises(PermissionError):
        retriever.search("banque", allowed_security_classifications=[], hard_filters={}, top_k=10, minimum_score=0)


def test_unknown_hard_filter_fails_closed():
    chunks = _chunks()
    retriever = SecureBM25Retriever(chunks, BM25Index.build(chunks["chunk_text"]), _phase5_filter_config())
    with pytest.raises(ValueError):
        retriever.search("banque", allowed_security_classifications=["INTERNAL"], hard_filters={"unknown": "x"}, top_k=10, minimum_score=0)


def test_recency_score_is_bounded():
    assert _recency_score("2020, 2021", 2026) == (2021, 0.75)
    assert _recency_score("", 2026) == (None, 0.25)
    assert _recency_score("2030", 2026) == (2026, 1.0)


def test_soft_preference_score():
    reference = {"country": "Tunisie", "sector": "Banque"}
    preferences = [
        {"field": "country", "value": "Tunisie"},
        {"field": "sector", "value": "Agriculture"},
    ]
    assert _soft_preference_score(reference, preferences) == 0.5
    assert _soft_preference_score(reference, []) == 1.0


def test_canonical_reference_filter_blocks_multi_reference_metadata_leakage():
    references = pd.DataFrame(
        [
            {"reference_id": "BANK", "sector": "Banque", "project_year": "2021"},
            {"reference_id": "UTILITY", "sector": "Entreprise Pub", "project_year": "2022"},
            {"reference_id": "OLD_BANK", "sector": "Banque", "project_year": "2018"},
        ]
    )
    assert eligible_reference_ids(references, {"sector": "Banque", "year_after": 2019}) == {"BANK"}


def _review() -> dict:
    return {
        "requirements": [
            {"requirement_id": "R1", "classification": "MUST", "requirement_text": "must"},
            {"requirement_id": "R2", "classification": "SHOULD", "requirement_text": "should"},
        ],
        "soft_preferences": [],
    }


def _references() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "reference_id": "REF1",
                "client": "Client A",
                "country": "Tunisie",
                "sector": "Banque",
                "offering": "SDSI",
                "service_nature": "Roadmap",
                "project_year": "2021",
                "attestation_available": "Oui",
                "evidence_available": True,
                "data_quality_status": "PASS",
            },
            {
                "reference_id": "REF2",
                "client": "Client B",
                "country": "Tunisie",
                "sector": "Banque",
                "offering": "Audit",
                "service_nature": "Audit",
                "project_year": "2010",
                "attestation_available": "Non",
                "evidence_available": True,
                "data_quality_status": "PASS",
            },
        ]
    )


def _evidence() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"reference_id": "REF1", "requirement_id": "R1", "requirement_relevance_score": 0.9, "document_type": "ATTESTATION", "data_quality_status": "PASS", "citation_uri": "u1", "chunk_id": "c1"},
            {"reference_id": "REF1", "requirement_id": "R2", "requirement_relevance_score": 0.8, "document_type": "ATTESTATION", "data_quality_status": "PASS", "citation_uri": "u2", "chunk_id": "c2"},
            {"reference_id": "REF2", "requirement_id": "R1", "requirement_relevance_score": 0.4, "document_type": "SPECIFICATION", "data_quality_status": "PASS", "citation_uri": "u3", "chunk_id": "c3"},
        ]
    )


def test_scoring_rewards_coverage_and_stronger_evidence(config):
    recommendations, coverage = score_references(review=_review(), evidence=_evidence(), references=_references(), config=config)
    assert recommendations.iloc[0]["reference_id"] == "REF1"
    assert recommendations.iloc[0]["must_covered"] == 1
    assert len(coverage) == 4


def test_missing_must_requirement_creates_warning(config):
    recommendations, _ = score_references(review=_review(), evidence=_evidence(), references=_references(), config=config)
    warning = recommendations.set_index("reference_id").loc["REF2", "warnings"]
    assert "MUST coverage" not in warning
    # REF2 covers MUST but misses SHOULD; warnings are intentionally MUST-only.


def test_diversity_limits_same_client(config):
    recommendations = pd.DataFrame(
        [
            {"reference_id": f"R{i}", "client": "Same" if i < 4 else "Other", "base_score": 1 - i / 10}
            for i in range(5)
        ]
    )
    diversified = diversify_recommendations(recommendations, config)
    assert diversified.head(3)["client"].tolist().count("Same") <= 2
    assert diversified["final_rank"].tolist() == list(range(1, len(diversified) + 1))


def test_gap_summary_reports_missing_requirement():
    requirements = [
        {"requirement_id": "R1", "classification": "MUST", "requirement_text": "x"},
        {"requirement_id": "R2", "classification": "SHOULD", "requirement_text": "y"},
    ]
    evidence = pd.DataFrame([{"requirement_id": "R1", "reference_id": "A", "requirement_relevance_score": 0.8}])
    gaps = requirement_gap_summary(requirements, evidence, 0.25)
    assert gaps[0]["gap"] is False and gaps[1]["gap"] is True


def test_evidence_validation_requires_complete_provenance():
    complete = pd.DataFrame(
        [
            {
                "reference_id": "R",
                "requirement_id": "Q",
                "document_id": "D",
                "chunk_id": "C",
                "chunk_text_sha256": "a",
                "source_sha256": "b",
                "page_number_1_based": 1,
                "citation_label": "label",
                "citation_uri": "uri",
                "evidence_excerpt": "text",
            }
        ]
    )
    assert validate_evidence(complete) == 1.0
    complete.loc[0, "citation_uri"] = ""
    with pytest.raises(AssertionError):
        validate_evidence(complete)


def test_empty_evidence_has_zero_coverage():
    assert validate_evidence(pd.DataFrame()) == 0.0


def test_review_workbook_has_human_shortlist_control(tmp_path):
    recommendations, coverage = score_references(review=_review(), evidence=_evidence(), references=_references(), config=load_phase7_config(CONFIG_PATH))
    recommendations = diversify_recommendations(recommendations, load_phase7_config(CONFIG_PATH))
    full_evidence = pd.DataFrame(
        [
            {
                "reference_id": "REF1", "requirement_id": "R1", "source_file_name": "x.pdf",
                "page_number_1_based": 1, "evidence_excerpt": "text", "citation_label": "x p1",
                "citation_uri": "uri", "chunk_id": "c", "source_sha256": "a", "chunk_text_sha256": "b",
            }
        ]
    )
    manifest = {"status": "TEST", "opportunity_id": "O", "retrieval_mode": "bm25", "recommendations": len(recommendations), "requirement_gaps": 0, "citation_coverage": 1.0, "external_llm_calls": 0, "cross_encoder_calls": 0}
    path = tmp_path / "review.xlsx"
    create_recommendation_workbook(path, recommendations, coverage, full_evidence, [], manifest)
    workbook = openpyxl.load_workbook(path)
    assert workbook.sheetnames == ["Overview", "Ranked References", "Requirement Coverage", "Evidence", "Requirement Gaps"]
    assert workbook["Ranked References"]["N2"].value == "PENDING"


def test_phase5_index_verification_detects_tampering(tmp_path, config):
    root = tmp_path / "phase5"
    root.mkdir()
    manifest = {"status": "TECHNICAL_PASS", "qa_gate": "PASS"}
    (root / "PHASE_5_MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")
    (root / "SHA256SUMS.txt").write_text("x", encoding="utf-8")
    (root / "_SUCCESS.json").write_text(json.dumps({"manifest_sha256": "bad"}), encoding="utf-8")
    with pytest.raises(AssertionError):
        verify_phase5_index(root, config)
