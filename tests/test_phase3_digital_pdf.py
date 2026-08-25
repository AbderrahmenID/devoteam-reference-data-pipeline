from pathlib import Path

import fitz

from devoteam_reference_ai.phase3_extraction import process_document


CONFIG = {
    "pipeline_version": "phase3_extract_v1",
    "input": {"snapshot_id": "snapshot"},
    "extraction": {
        "digital_text_min_characters": 80,
        "digital_text_min_words": 10,
        "pdf_render_dpi": 150,
        "ocr_languages": "fra+eng+ara",
        "tesseract_psm": 3,
        "blank_ink_ratio_threshold": 0.001,
        "office_conversion_timeout_seconds": 5,
    },
    "quality": {
        "pass_min_characters": 80,
        "review_min_characters": 20,
        "ocr_pass_min_confidence": 60,
        "ocr_review_min_confidence": 35,
    },
    "security": {
        "classification": "INTERNAL",
        "persist_raw_text": True,
        "redact_email": True,
        "redact_phone_like_numbers": True,
        "redact_iban": True,
        "redact_monetary_amounts": True,
    },
}


def test_digital_pdf_avoids_unnecessary_ocr(tmp_path: Path):
    path = tmp_path / "evidence.pdf"
    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_textbox(
        fitz.Rect(40, 40, 550, 700),
        "Attestation de référence Devoteam pour une mission de transformation numérique. " * 4,
        fontsize=11,
    )
    pdf.save(path)
    pdf.close()
    document = {
        "file_id": "drive-file-id",
        "name": "evidence.pdf",
        "mimeType": "application/pdf",
        "local_sha256": "abc",
        "local_relative_path": "raw/evidence/evidence.pdf",
    }
    summary, pages = process_document(path, document, CONFIG)
    assert summary["status"] == "COMPLETE"
    assert pages[0]["extraction_method"] == "digital_pdf"
    assert pages[0]["document_id"] == "drive-file-id"
    assert pages[0]["qa_status"] == "PASS"
