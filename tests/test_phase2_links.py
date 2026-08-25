from pathlib import Path

from openpyxl import Workbook

from devoteam_reference_ai.phase2_links import discover_drive_links


CONFIG = {
    "source": {"master_workbook": {"sheet_candidates": ["BDOD"], "header_scan_rows": 5}},
    "exclusions": {
        "never_ingest_headers": ["Valeur Projet", "Équipe Intervenante"],
        "never_follow_link_headers": ["Site web", "Logo"],
    },
}


def test_link_discovery_deduplicates_channels_and_skips_blocked_columns(tmp_path: Path):
    file_id = "1AbCdEfGhIjKlMnOpQrStUvWxYz12"
    secret_id = "1ZZZZZZZZZZZZZZZZZZZZZZZZZZZZ"
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "BDOD"
    sheet.append(["#Réf", "Client", "Pays", "Offre", "Année", "Attestation", "Valeur Projet", "Site web"])
    sheet.append([1, "Client", "TN", "Audit", 2024, f"https://drive.google.com/file/d/{file_id}/view", f"https://drive.google.com/file/d/{secret_id}/view", f"https://drive.google.com/file/d/{secret_id}/view"])
    sheet["F2"].hyperlink = f"https://drive.google.com/file/d/{file_id}/view"
    path = tmp_path / "source.xlsx"
    workbook.save(path)
    result = discover_drive_links(path, CONFIG)
    assert len(result["records"]) == 1
    assert result["records"][0]["target_file_id"] == file_id
    assert result["records"][0]["channels"] == "cell_value,hyperlink"
    assert "Valeur Projet" in result["blocked_headers_present"]
    assert secret_id not in str(result)
