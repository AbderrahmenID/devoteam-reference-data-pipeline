import json
from pathlib import Path

import openpyxl
import pandas as pd
import pytest

from devoteam_reference_ai.phase4_corpus import (
    build_reference_catalog,
    chunk_page_text,
    classify_document,
    clean_redacted_text,
    detect_language,
    load_phase4_config,
)


CONFIG_PATH = Path(__file__).parents[1] / "config" / "phase4_corpus.yaml"


@pytest.fixture()
def config():
    return load_phase4_config(CONFIG_PATH)


def test_config_disables_external_models_and_raw_output(config):
    assert config["security"]["external_llm_enabled"] is False
    assert config["security"]["raw_text_allowed_in_outputs"] is False
    assert config["security"]["source_mutation_allowed"] is False
    assert config["cleaning"]["source_text_column"] == "text_redacted"
    assert config["chunking"]["page_constrained"] is True


def test_cleaning_is_conservative_and_preserves_redaction(config):
    raw = "Mission de transfor-\nmation\n---\n\nContact [REDACTED_EMAIL]\x00\n"
    assert clean_redacted_text(raw, config) == (
        "Mission de transformation\n\nContact [REDACTED_EMAIL]"
    )


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Le projet est réalisé pour le client et les équipes.", "fr"),
        ("The project is delivered for the client and their teams.", "en"),
        ("هذا عقد لتنفيذ مشروع التحول الرقمي للمؤسسة", "ar"),
        ("Le projet pour le client. هذا عقد للمؤسسة العربية.", "fr-ar"),
    ],
)
def test_language_detection(text, expected):
    assert detect_language(text) == expected


@pytest.mark.parametrize(
    ("filename", "text", "expected"),
    [
        ("preuve.pdf", "Attestation de référence", "ATTESTATION"),
        ("PV.pdf", "Procès-verbal de réception", "MINUTES"),
        ("dossier.pdf", "Cahier des charges", "SPECIFICATION"),
        ("CONTRAT.pdf", "Conditions générales", "CONTRACT"),
        ("preuve.pdf", "Description générale de la mission", "OTHER_EVIDENCE"),
    ],
)
def test_document_type_is_deterministic(filename, text, expected):
    assert classify_document(filename, text)[0] == expected


def test_chunks_are_stable_bounded_and_offset_reproducible(config):
    text = "\n\n".join(
        f"Section {index}. " + ("Transformation numérique et gouvernance. " * 12)
        for index in range(10)
    )
    first = chunk_page_text(text, config)
    second = chunk_page_text(text, config)
    assert first == second
    assert len(first) > 1
    assert all(len(chunk) <= config["chunking"]["max_characters"] for _, _, chunk in first)
    assert all(text[start:end] == chunk for start, end, chunk in first)
    assert all(first[index][0] < first[index - 1][1] for index in range(1, len(first)))


def test_reference_catalog_uses_only_allowlisted_fields(tmp_path, config):
    workbook_path = tmp_path / "master.xlsx"
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "BDOD"
    headers = [
        "N°", "#Réf", "Pays", "BU", "Nom de domaine de l'entreprise", "Logo",
        "Client", "Secteur", "Nature de la Prestation", "Financement ", "Offre",
        "Année de Réalisation", "Valeur Projet", "Equipe Intervenante",
        "Attestation de référence", "Commentaire",
    ]
    sheet.append(headers)
    sheet.append([
        7, "link", "Tunisie", "MENA", "example.tn", "", "Client A", "Banque",
        "Transformation", "Interne", "Cloud", "2021", "SECRET_VALUE",
        "SECRET_TEAM", "Oui", "SECRET_COMMENT",
    ])
    workbook.save(workbook_path)

    links_path = tmp_path / "links.csv"
    pd.DataFrame([{
        "cell_coordinate": "B2", "channels": "hyperlink", "column_number": "2",
        "row_number": "2", "sheet": "BDOD", "source_header": "#Réf",
        "target_file_id": "shortcut-1",
    }]).to_csv(links_path, index=False)
    targets_path = tmp_path / "targets.csv"
    pd.DataFrame([{
        "target_file_id": "shortcut-1", "resolved_file_id": "document-1",
        "snapshot_status": "SNAPSHOTTED", "name": "proof.pdf",
    }]).to_csv(targets_path, index=False)

    catalog = build_reference_catalog(
        master_path=workbook_path,
        evidence_links_path=links_path,
        evidence_targets_path=targets_path,
        document_ids={"document-1"},
        config=config,
    )
    assert len(catalog) == 1
    assert bool(catalog.loc[0, "evidence_available"])
    assert catalog.loc[0, "client"] == "Client A"
    normalized = " ".join(catalog.columns).casefold()
    assert "valeur projet" not in normalized
    assert "equipe intervenante" not in normalized
    assert "commentaire" not in normalized
    assert "SECRET_VALUE" not in json.dumps(catalog.to_dict(orient="records"))
