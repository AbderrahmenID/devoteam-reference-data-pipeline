import hashlib
import json
from pathlib import Path

from PIL import Image

from devoteam_reference_ai import phase3_1_repair as repair


def test_quality_contract_does_not_force_low_volume_pages_to_pass():
    config = {
        "quality": {
            "pass_min_characters": 80,
            "review_min_characters": 20,
            "pass_min_words": 10,
            "ocr_pass_min_confidence": 60,
            "ocr_review_min_confidence": 35,
        }
    }
    assert repair._classification({"character_count": 120, "word_count": 20}, 82, config)[0] == "PASS"
    assert repair._classification({"character_count": 120, "word_count": 20}, 48, config)[0] == "REVIEW"
    assert repair._classification({"character_count": 58, "word_count": 10}, 95, config)[0] == "REVIEW"
    assert repair._classification({"character_count": 5, "word_count": 1}, 95, config)[0] == "FAILED"


def test_attempt_plan_is_bounded_and_failed_pages_get_orientation_retry():
    config = {
        "repair": {
            "latin_languages": "fra+eng",
            "arabic_languages": "ara+fra",
            "mixed_languages": "fra+eng+ara",
            "max_attempts_per_page": 6,
        }
    }
    specs = repair._attempt_specs(
        {"qa_status": "FAILED", "arabic_character_count": 0}, False, config
    )
    assert len(specs) == 6
    assert specs[0]["languages"] == "fra+eng"
    assert any(spec.get("rotation") == 90 for spec in specs)


def test_repair_page_can_recover_image_only_slide_from_native_text(monkeypatch):
    image = Image.new("RGB", (500, 300), "white")
    native = (
        "Attestation de référence Devoteam pour une mission de transformation "
        "digitale réalisée avec succès auprès du client partenaire."
    )
    monkeypatch.setattr(repair, "_load_source_page", lambda *_: ([image], native))
    original = {
        "document_id": "doc-1",
        "source_file_name": "reference.pptx",
        "source_mime_type": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "source_sha256": "a" * 64,
        "source_relative_path": "raw/evidence/reference.pptx",
        "page_number_1_based": 1,
        "pipeline_version": "phase3_extract_v1",
        "extraction_method": "pptx_native_fallback",
        "ocr_engine": "",
        "ocr_languages": "",
        "ocr_confidence": None,
        "arabic_character_count": 0,
        "qa_status": "FAILED",
        "text_raw": "",
    }
    config = {
        "pipeline_version": "phase3_1_targeted_repair_v1",
        "repair": {
            "latin_languages": "fra+eng",
            "arabic_languages": "ara+fra",
            "mixed_languages": "fra+eng+ara",
            "max_attempts_per_page": 6,
            "early_stop_confidence": 78,
        },
        "quality": {
            "pass_min_characters": 80,
            "review_min_characters": 20,
            "pass_min_words": 10,
            "ocr_pass_min_confidence": 60,
            "ocr_review_min_confidence": 35,
        },
        "security": {
            "persist_raw_text": True,
            "redact_email": True,
            "redact_phone_like_numbers": True,
            "redact_iban": True,
            "redact_monetary_amounts": True,
        },
    }
    page, attempts, _ = repair.repair_page(Path("unused"), original, config)
    assert page["qa_status"] == "PASS"
    assert page["retrieval_eligible"] is True
    assert page["extraction_method"] == "targeted_native_slide"
    assert len(attempts) == 2


def test_verify_phase3_1_checks_hashes_and_pinned_counts(tmp_path):
    manifest = {
        "status": "PASS",
        "pages_targeted": 21,
        "curated_pages_total": 408,
        "repair_processing_failures": 0,
        "source_snapshot_mutation_calls": 0,
        "phase3_output_mutation_calls": 0,
        "external_llm_calls": 0,
    }
    manifest_path = tmp_path / "PHASE_3_1_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    payload = tmp_path / "payload.txt"
    payload.write_text("validated", encoding="utf-8")
    payload_hash = hashlib.sha256(payload.read_bytes()).hexdigest()
    sums = tmp_path / "SHA256SUMS.txt"
    sums.write_text(f"{payload_hash}  payload.txt\n", encoding="utf-8")
    success = {
        "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "sha256sums_sha256": hashlib.sha256(sums.read_bytes()).hexdigest(),
    }
    (tmp_path / "_SUCCESS.json").write_text(json.dumps(success), encoding="utf-8")
    assert repair.verify_phase3_1(tmp_path)["pages_targeted"] == 21
