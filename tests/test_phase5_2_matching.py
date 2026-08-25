from __future__ import annotations

import copy
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from devoteam_reference_ai.phase5_bm25 import BM25Index
from devoteam_reference_ai.phase5_2_matching import (
    HardenedMatchingEngine,
    build_reference_contract,
    canonical_country,
    citation_metrics,
    compile_phase6_controls,
    create_citation_audit_workbook,
    facet_counts,
    filter_reference_contract,
    load_phase5_2_config,
    parse_year_interval,
    safe_spreadsheet_value,
    score_matches,
    sha256_text,
    split_policy_requirements,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "config" / "phase5_2_matching_hardening.yaml"


@pytest.fixture()
def config() -> dict:
    return load_phase5_2_config(CONFIG_PATH)


def _documents() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "document_id": "D1",
                "source_file_name": "attestation.pdf",
                "source_sha256": "a" * 64,
                "security_classification": "INTERNAL",
                "document_type": "ATTESTATION",
                "document_language": "fr",
                "retrieval_eligible": True,
            },
            {
                "document_id": "D2",
                "source_file_name": "secret.pdf",
                "source_sha256": "b" * 64,
                "security_classification": "RESTRICTED",
                "document_type": "CONTRACT",
                "document_language": "fr",
                "retrieval_eligible": True,
            },
            {
                "document_id": "D3",
                "source_file_name": "other.pdf",
                "source_sha256": "c" * 64,
                "security_classification": "INTERNAL",
                "document_type": "ATTESTATION",
                "document_language": "en",
                "retrieval_eligible": True,
            },
        ]
    )


def _references() -> pd.DataFrame:
    base = {
        "sheet": "Sheet1",
        "cell_coordinate": "A1",
        "target_file_id": "",
        "snapshot_status": "CANDIDATE_FILE",
        "target_name": "",
        "business_unit": "Digital impulse",
        "company_domain": "",
        "funding": "",
    }
    return pd.DataFrame(
        [
            {
                **base,
                "reference_id": "R1",
                "row_number": 2,
                "canonical_document_id": "D1",
                "evidence_available": True,
                "reference_number": "#VALUE!",
                "country": "tunisie",
                "client": "Banque A",
                "sector": "Banque",
                "service_nature": "Stratégie digitale, gouvernance, architecture cible et API Gateway",
                "offering": "SDSI",
                "project_year": "2020, 2021",
                "attestation_available": "Attestation Originale",
                "data_quality_status": "PASS",
                "document_retrieval_eligible": True,
            },
            {
                **base,
                "reference_id": "R1-BIS",
                "row_number": 3,
                "canonical_document_id": "D1",
                "evidence_available": True,
                "reference_number": "2",
                "country": "Tunisie",
                "client": "Banque A",
                "sector": "Banque",
                "service_nature": "Stratégie digitale, gouvernance, architecture cible et API Gateway",
                "offering": "SDSI",
                "project_year": "2020–2021",
                "attestation_available": "Attestation Scannée",
                "data_quality_status": "PASS",
                "document_retrieval_eligible": True,
            },
            {
                **base,
                "reference_id": "R2",
                "row_number": 4,
                "canonical_document_id": "D2",
                "evidence_available": True,
                "reference_number": "3",
                "country": "Abidjan",
                "client": "Banque B",
                "sector": "Banque",
                "service_nature": "Cloud et gouvernance des données",
                "offering": "Cloud",
                "project_year": "2022–Présent",
                "attestation_available": "Contrat",
                "data_quality_status": "PASS",
                "document_retrieval_eligible": True,
            },
            {
                **base,
                "reference_id": "R3",
                "row_number": 5,
                "canonical_document_id": "D3",
                "evidence_available": False,
                "reference_number": "4",
                "country": "Maroc",
                "client": "Entreprise C",
                "sector": "Industrie",
                "service_nature": "Audit de sécurité",
                "offering": "Cyber Security",
                "project_year": "2018",
                "attestation_available": "Sans JUSTIF",
                "data_quality_status": "MISSING_EVIDENCE",
                "document_retrieval_eligible": False,
            },
        ]
    )


@pytest.fixture()
def contract(config) -> pd.DataFrame:
    frame, _ = build_reference_contract(_references(), _documents(), config)
    return frame


def _chunks() -> pd.DataFrame:
    texts = [
        "La mission couvre la gouvernance, l'architecture cible et la feuille de route bancaire.",
        "Document hautement confidentiel sur une architecture cible bancaire.",
        "Audit de sécurité et continuité pour une entreprise industrielle.",
    ]
    rows = []
    for index, (document_id, text, classification, source_hash) in enumerate(
        [
            ("D1", texts[0], "INTERNAL", "a" * 64),
            ("D2", texts[1], "RESTRICTED", "b" * 64),
            ("D3", texts[2], "INTERNAL", "c" * 64),
        ]
    ):
        rows.append(
            {
                "vector_row": index,
                "chunk_id": f"C{index + 1}",
                "document_id": document_id,
                "security_classification": classification,
                "chunk_text": text,
                "chunk_text_sha256": sha256_text(text),
                "source_sha256": source_hash,
                "source_file_name": f"{document_id}.pdf",
                "page_number_1_based": 1,
                "citation_label": f"{document_id}.pdf — page 1",
                "citation_uri": f"https://drive.google.com/file/d/{document_id}/view#page=1",
                "document_type": "ATTESTATION",
                "data_quality_status": "PASS",
            }
        )
    return pd.DataFrame(rows)


@pytest.fixture()
def engine(contract, config) -> HardenedMatchingEngine:
    chunks = _chunks()
    bm25 = BM25Index.build(chunks["chunk_text"].tolist(), k1=1.2, b=0.75)
    embeddings = np.asarray(
        [
            [1.0, 0.0],
            [0.98, 0.2],
            [0.0, 1.0],
        ],
        dtype=np.float32,
    )
    embeddings /= np.linalg.norm(embeddings, axis=1, keepdims=True)
    return HardenedMatchingEngine(
        chunks=chunks,
        bm25=bm25,
        embeddings=embeddings,
        reference_contract=contract,
        config=config,
    )


def test_config_keeps_security_and_promotion_gates(config):
    assert config["security"]["authorization_before_scoring_required"] is True
    assert config["evaluation"]["expert_gold_set_required_for_promotion"] is True
    assert config["retrieval"]["reranking"]["cross_encoder_enabled"] is False


def test_config_rejects_external_embedding_api(tmp_path):
    raw = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    raw["security"]["external_embedding_api_enabled"] = True
    path = tmp_path / "bad.yaml"
    path.write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")
    with pytest.raises(ValueError, match="security defaults"):
        load_phase5_2_config(path)


@pytest.mark.parametrize(
    "value",
    ["=1+1", "+CMD", "-2+3", "@SUM(A1:A2)", " =HYPERLINK(\"x\")"],
)
def test_spreadsheet_formula_injection_is_neutralized(value):
    assert safe_spreadsheet_value(value).startswith("'")


def test_plain_spreadsheet_text_is_preserved():
    assert safe_spreadsheet_value("normal text") == "normal text"


def test_year_interval_handles_range_and_ongoing(config):
    completed = parse_year_interval("2019, 2021", config)
    ongoing = parse_year_interval("2024–Présent", config)
    assert (completed["year_start"], completed["year_end"]) == (2019, 2021)
    assert ongoing["year_start"] == 2024
    assert ongoing["ongoing"] is True
    assert ongoing["project_status"] == "ONGOING"


@pytest.mark.parametrize(
    ("raw", "code"),
    [
        ("Tunise", "TN"),
        ("tunisie", "TN"),
        ("Abidjan", "CI"),
        ("Côte d’Ivoire", "CI"),
        ("libya", "LY"),
    ],
)
def test_country_aliases_are_canonical(raw, code, config):
    assert canonical_country(raw, config)["country_code"] == code


def test_reference_contract_preserves_raw_values_and_adds_stable_fields(config):
    contract, issues = build_reference_contract(_references(), _documents(), config)
    row = contract.set_index("reference_id").loc["R1"]
    assert row["reference_number_raw"] == "#VALUE!"
    assert row["display_reference_id"].startswith("REF-")
    assert row["country_code"] == "TN"
    assert row["sector_code"] == "BANKING"
    assert row["offering_code"] == "IT_STRATEGY"
    assert json.loads(row["technology_tags_json"]) == ["API_MANAGEMENT"]
    assert {"IT_GOVERNANCE", "TARGET_ARCHITECTURE"} <= set(
        json.loads(row["capability_tags_json"])
    )
    assert "INVALID_SOURCE_REFERENCE_NUMBER" in set(issues["issue_code"])


def test_same_evidence_document_forms_one_duplicate_group(contract):
    rows = contract.set_index("reference_id")
    assert rows.loc["R1", "duplicate_group_id"] == rows.loc["R1-BIS", "duplicate_group_id"]
    assert rows.loc["R1", "duplicate_group_size"] == 2


def test_filters_use_date_overlap_and_normalized_location(contract, config):
    filtered, audit = filter_reference_contract(
        contract,
        allowed_security_classifications=["INTERNAL", "RESTRICTED"],
        hard_filters={"country_code": "Tunisie", "year_from": 2020, "year_to": 2021},
        exclusions=[],
        config=config,
    )
    assert set(filtered["reference_id"]) == {"R1", "R1-BIS"}
    assert audit["authorization_applied_before_scoring"] is True


def test_tag_filter_is_exact_controlled_facet(contract, config):
    filtered, _ = filter_reference_contract(
        contract,
        allowed_security_classifications=["INTERNAL", "RESTRICTED"],
        hard_filters={"technology_tags": ["API_MANAGEMENT"]},
        exclusions=[],
        config=config,
    )
    assert set(filtered["reference_id"]) == {"R1", "R1-BIS"}


def test_inaccessible_references_do_not_enter_facets(contract, config):
    filtered, _ = filter_reference_contract(
        contract,
        allowed_security_classifications=["INTERNAL"],
        hard_filters={},
        exclusions=[],
        config=config,
    )
    counts = facet_counts(filtered)
    assert "CI" not in counts["country_code"]
    assert counts["country_code"]["TN"] == 2


def test_explicit_exclusion_is_enforced(contract, config):
    exploratory = contract.copy()
    exploratory["base_shortlist_eligible"] = True
    filtered, audit = filter_reference_contract(
        exploratory,
        allowed_security_classifications=["INTERNAL", "RESTRICTED"],
        hard_filters={},
        exclusions=[{"field": "evidence_available", "operator": "is_false"}],
        config=config,
    )
    assert "R3" not in set(filtered["reference_id"])
    assert "R3" in audit["excluded_reference_ids"]


def test_unsupported_filter_fails_closed(contract, config):
    with pytest.raises(ValueError, match="Unsupported hard filters"):
        filter_reference_contract(
            contract,
            allowed_security_classifications=["INTERNAL"],
            hard_filters={"made_up_filter": "x"},
            exclusions=[],
            config=config,
        )


def test_evidence_policy_is_not_sent_as_semantic_query(config):
    requirements = [
        {
            "requirement_id": "R1",
            "classification": "MUST",
            "requirement_text": "Architecture cible et feuille de route",
        },
        {
            "requirement_id": "R2",
            "classification": "MUST",
            "requirement_text": "Les références sans document justificatif doivent être exclues.",
        },
    ]
    content, policies = split_policy_requirements(requirements, config)
    assert [row["requirement_id"] for row in content] == ["R1"]
    assert policies[0]["policy"] == "SUPPORTING_EVIDENCE_REQUIRED"


def test_phase6_controls_compile_hard_filters_and_exclusion(config):
    requirements = [
        {
            "requirement_id": "R1",
            "classification": "MUST",
            "requirement_text": "Les références sans document justificatif doivent être exclues.",
        }
    ]
    proposals = [
        {
            "field": "sector",
            "value": "Banque",
            "proposed_behavior": "HARD_CANDIDATE",
        },
        {
            "field": "year_after",
            "value": 2019,
            "proposed_behavior": "HARD_CANDIDATE",
        },
    ]
    controls = compile_phase6_controls(requirements, proposals, config)
    assert controls["hard_filters"] == {"sector_code": "BANKING", "year_from": 2019}
    assert controls["exclusions"][0]["field"] == "evidence_available"


def test_authorization_is_applied_before_any_scoring(engine):
    results, eligible, audit = engine.search_chunks(
        "architecture cible bancaire",
        allowed_security_classifications=["INTERNAL"],
        hard_filters={"sector_code": "BANKING", "year_from": 2019},
        mode="hybrid",
        query_vector=np.asarray([1.0, 0.0], dtype=np.float32),
    )
    assert set(results["document_id"]) == {"D1"}
    assert set(eligible["reference_id"]) == {"R1", "R1-BIS"}
    assert audit["authorization_applied_before_scoring"] is True
    assert audit["all_scored_rows_authorized"] is True


def test_dense_query_vector_must_be_normalized(engine):
    with pytest.raises(ValueError, match="unit vector"):
        engine.search_chunks(
            "architecture",
            allowed_security_classifications=["INTERNAL"],
            mode="dense",
            query_vector=np.asarray([2.0, 0.0], dtype=np.float32),
        )


def _score_fixture(contract: pd.DataFrame) -> tuple[list[dict], pd.DataFrame, pd.DataFrame]:
    requirements = [
        {"requirement_id": "M1", "classification": "MUST", "requirement_text": "architecture"},
        {"requirement_id": "M2", "classification": "MUST", "requirement_text": "roadmap"},
    ]
    eligible = contract.loc[contract["reference_id"].isin(["R1", "R1-BIS"])].copy()
    evidence = pd.DataFrame(
        [
            {
                "reference_id": "R1",
                "requirement_id": "M1",
                "rerank_score": 0.9,
                "citation_uri": "https://x",
                "chunk_id": "C1",
                "retrieval_mode": "hybrid",
            },
            {
                "reference_id": "R1",
                "requirement_id": "M2",
                "rerank_score": 0.8,
                "citation_uri": "https://x",
                "chunk_id": "C1",
                "retrieval_mode": "hybrid",
            },
            {
                "reference_id": "R1-BIS",
                "requirement_id": "M1",
                "rerank_score": 0.95,
                "citation_uri": "https://x",
                "chunk_id": "C1",
                "retrieval_mode": "hybrid",
            },
        ]
    )
    return requirements, evidence, eligible


def test_must_gate_blocks_incomplete_reference(contract, config):
    requirements, evidence, eligible = _score_fixture(contract)
    recommendations, ineligible, _ = score_matches(
        requirements=requirements,
        evidence=evidence,
        eligible_contract=eligible,
        soft_preferences=[],
        config=config,
    )
    assert set(recommendations["reference_id"]) == {"R1"}
    blocked = ineligible.set_index("reference_id").loc["R1-BIS"]
    assert blocked["eligibility_reasons"] == "MISSING_MUST:1/2"


def test_duplicate_group_never_occupies_two_shortlist_slots(contract, config):
    requirements = [
        {"requirement_id": "M1", "classification": "MUST", "requirement_text": "architecture"}
    ]
    eligible = contract.loc[contract["reference_id"].isin(["R1", "R1-BIS"])].copy()
    evidence = pd.DataFrame(
        [
            {
                "reference_id": reference_id,
                "requirement_id": "M1",
                "rerank_score": score,
                "citation_uri": "https://x",
                "chunk_id": "C1",
                "retrieval_mode": "hybrid",
            }
            for reference_id, score in [("R1", 0.9), ("R1-BIS", 0.8)]
        ]
    )
    recommendations, ineligible, _ = score_matches(
        requirements=requirements,
        evidence=evidence,
        eligible_contract=eligible,
        soft_preferences=[],
        config=config,
    )
    assert len(recommendations) == 1
    assert ineligible.iloc[0]["eligibility_reasons"] == "DUPLICATE_GROUP_SUPPRESSED"


def _citation_frame() -> pd.DataFrame:
    text = "Architecture cible et feuille de route."
    return pd.DataFrame(
        [
            {
                "reference_id": "R1",
                "requirement_id": "M1",
                "requirement_classification": "MUST",
                "requirement_text": "architecture cible",
                "document_id": "D1",
                "document_type": "ATTESTATION",
                "data_quality_status": "PASS",
                "security_classification": "INTERNAL",
                "chunk_id": "C1",
                "chunk_text": text,
                "chunk_text_sha256": sha256_text(text),
                "source_sha256": "a" * 64,
                "source_file_name": "=MALICIOUS.pdf",
                "page_number_1_based": 1,
                "citation_label": "D1 page 1",
                "citation_uri": "https://drive.google.com/file/d/D1/view#page=1",
                "retrieval_mode": "hybrid",
                "retrieval_rank": 1,
                "retrieval_score": 1.0,
                "retrieval_score_normalized": 1.0,
                "term_coverage": 1.0,
                "rerank_score": 1.0,
            }
        ]
    )


def test_citation_completeness_and_integrity_are_separate():
    evidence = _citation_frame()
    metrics = citation_metrics(evidence)
    assert metrics["citation_completeness"] == 1.0
    assert metrics["citation_integrity"] == 1.0
    assert metrics["citation_correctness_status"] == "PENDING_HUMAN_AUDIT"
    evidence.loc[0, "chunk_text_sha256"] = "0" * 64
    changed = citation_metrics(evidence)
    assert changed["citation_completeness"] == 1.0
    assert changed["citation_integrity"] == 0.0


def test_citation_audit_workbook_serializes_untrusted_text_safely(tmp_path):
    import openpyxl

    path = tmp_path / "audit.xlsx"
    create_citation_audit_workbook(path, _citation_frame(), sample_size=10)
    workbook = openpyxl.load_workbook(path, data_only=False)
    sheet = workbook["Citation Audit"]
    assert sheet["E2"].value == "'=MALICIOUS.pdf"
    assert sheet["K2"].value == "PENDING"


def test_full_match_returns_only_authorized_must_complete_reference(engine):
    requirements = [
        {
            "requirement_id": "M1",
            "classification": "MUST",
            "requirement_text": "gouvernance architecture cible feuille de route bancaire",
        }
    ]
    result = engine.match(
        requirements,
        allowed_security_classifications=["INTERNAL"],
        hard_filters={"sector_code": "BANKING", "year_from": 2019},
        mode="hybrid",
        query_vectors={"M1": np.asarray([1.0, 0.0], dtype=np.float32)},
    )
    assert len(result.recommendations) == 1
    assert result.recommendations.iloc[0]["canonical_document_id"] == "D1"
    assert result.recommendations.iloc[0]["must_covered"] == 1
    assert result.filter_audit["external_embedding_api_calls"] == 0
