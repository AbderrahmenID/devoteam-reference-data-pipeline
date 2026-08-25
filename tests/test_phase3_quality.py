from PIL import Image

from devoteam_reference_ai.phase3_quality import image_ink_ratio, normalize_extracted_text, page_quality, text_metrics


CONFIG = {"quality": {
    "pass_min_characters": 80,
    "review_min_characters": 20,
    "ocr_pass_min_confidence": 60,
    "ocr_review_min_confidence": 35,
}}


def test_normalization_preserves_lines_and_arabic():
    value = normalize_extracted_text("  Bonjour   monde \n\n\n مرحبا بالعالم  ")
    assert value == "Bonjour monde\n\nمرحبا بالعالم"


def test_blank_image_has_zero_ink():
    assert image_ink_ratio(Image.new("RGB", (100, 100), "white")) == 0.0


def test_quality_is_automatic_not_three_line_checkpoint():
    metrics = text_metrics("A " * 60)
    status, _ = page_quality("digital_pdf", metrics, None, False, CONFIG)
    assert status == "PASS"
