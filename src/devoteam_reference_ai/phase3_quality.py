from __future__ import annotations

import re
import unicodedata
from typing import Any

from PIL import Image, ImageOps, ImageStat


WORD_RE = re.compile(r"\w+", re.UNICODE)


def normalize_extracted_text(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or ""))
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "".join(ch for ch in text if ch in "\n\t" or unicodedata.category(ch)[0] != "C")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    compact: list[str] = []
    blank = False
    for line in lines:
        if line:
            compact.append(line)
            blank = False
        elif not blank and compact:
            compact.append("")
            blank = True
    return "\n".join(compact).strip()


def text_metrics(text: str) -> dict[str, int]:
    normalized = normalize_extracted_text(text)
    return {
        "character_count": len(normalized),
        "word_count": len(WORD_RE.findall(normalized)),
        "line_count": sum(bool(line.strip()) for line in normalized.splitlines()),
        "latin_character_count": sum("LATIN" in unicodedata.name(ch, "") for ch in normalized),
        "arabic_character_count": sum("ARABIC" in unicodedata.name(ch, "") for ch in normalized),
    }


def image_ink_ratio(image: Image.Image) -> float:
    gray = ImageOps.grayscale(ImageOps.exif_transpose(image.copy()))
    gray.thumbnail((1200, 1200))
    histogram = gray.histogram()
    ink = sum(histogram[:245])
    total = max(sum(histogram), 1)
    return float(ink / total)


def is_usable_digital_text(text: str, config: dict) -> bool:
    metrics = text_metrics(text)
    settings = config["extraction"]
    return (
        metrics["character_count"] >= int(settings["digital_text_min_characters"])
        and metrics["word_count"] >= int(settings["digital_text_min_words"])
    )


def page_quality(
    method: str,
    metrics: dict[str, int],
    ocr_confidence: float | None,
    is_blank: bool,
    config: dict,
) -> tuple[str, list[str]]:
    if is_blank and metrics["character_count"] < 10:
        return "BLANK", ["visually_blank_page"]
    quality = config["quality"]
    chars = metrics["character_count"]
    reasons: list[str] = []
    if chars < int(quality["review_min_characters"]):
        reasons.append("very_low_text_volume")
        return "FAILED", reasons
    if chars < int(quality["pass_min_characters"]):
        reasons.append("low_text_volume")
        return "REVIEW", reasons
    if method == "tesseract_ocr":
        confidence = float(ocr_confidence or 0.0)
        if confidence < float(quality["ocr_review_min_confidence"]):
            reasons.append("very_low_ocr_confidence")
            return "FAILED", reasons
        if confidence < float(quality["ocr_pass_min_confidence"]):
            reasons.append("low_ocr_confidence")
            return "REVIEW", reasons
    return "PASS", reasons
